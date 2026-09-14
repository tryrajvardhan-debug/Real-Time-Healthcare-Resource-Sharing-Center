# apps/calls/views.py
# replace all the webhook views with these fixed versions

import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status

from .models import CallLog, CallSession
from .services import (
    make_transfer_notification_call,
    make_transfer_alert_call,
    make_user_agent_call,
    build_transfer_twiml,
    build_transfer_alert_twiml,
    build_language_select_twiml,
    build_agent_listen_twiml,
    build_agent_end_twiml,
)
from .agent import ask_groq, detect_city_from_text, detect_language_from_speech
from apps.patients.models import TransferRequest


# apps/calls/views.py
# 1. Add this SMS function near the top after imports:

# apps/calls/views.py

def send_sms(to_number: str, message: str) -> tuple[bool, str]:
    """Returns (success: bool, error_message: str)"""
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException

    # ensure correct format
    phone = to_number.strip()
    if not phone.startswith('+'):
        phone = f'+91{phone}'

    try:
        c = TwilioClient(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        msg = c.messages.create(
            body  = message,
            from_ = settings.TWILIO_PHONE_NUMBER,
            to    = phone,
        )
        print(f'SMS sent OK — SID: {msg.sid} to {phone}')
        return True, ''

    except TwilioRestException as e:
        print(f'Twilio SMS error {e.code}: {e.msg}')
        return False, str(e.msg)

    except Exception as e:
        print(f'SMS general error: {e}')
        return False, str(e)
# ─────────────────────────────────────────────────────────────
#  Initiation endpoints
# ─────────────────────────────────────────────────────────────

class InitiateTransferCallView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, transfer_id):
        try:
            transfer = TransferRequest.objects.select_related(
                'patient', 'from_hospital', 'to_hospital'
            ).get(pk=transfer_id, status='accepted')
        except TransferRequest.DoesNotExist:
            return Response({'error': 'Accepted transfer not found'}, status=404)

        to_hospital = transfer.to_hospital
        if not to_hospital or not to_hospital.phone:
            return Response({'error': 'Receiving hospital has no phone number'}, status=400)

        phone = to_hospital.phone.strip().replace(' ', '').replace('-', '')
        if not phone.startswith('+'):
            phone = f'+91{phone}'

        call_log = CallLog.objects.create(
            call_type        = CallLog.CallType.TRANSFER_NOTIFICATION,
            to_number        = phone,
            transfer_request = transfer,
        )

        try:
            sid = make_transfer_notification_call(phone, str(transfer_id))
            call_log.twilio_call_sid = sid
            call_log.status          = CallLog.Status.RINGING
            call_log.save()
            return Response({
                'message'   : 'Transfer notification call initiated',
                'call_id'   : str(call_log.id),
                'calling'   : to_hospital.name,
                'phone'     : phone,
                'twilio_sid': sid,
            })
        except Exception as e:
            call_log.status = CallLog.Status.FAILED
            call_log.save()
            return Response({'error': str(e)}, status=500)


class RequestUserAgentCallView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone', '').strip().replace(' ', '').replace('-', '')
        city  = request.data.get('city', '').strip()

        if not phone:
            return Response({'error': 'Phone number is required'}, status=400)

        if not phone.startswith('+'):
            phone = f'+91{phone}'

        call_log = CallLog.objects.create(
            call_type = CallLog.CallType.USER_AGENT,
            to_number = phone,
        )
        session = CallSession.objects.create(
            call_log             = call_log,
            twilio_call_sid      = '',
            user_city            = city or None,
            conversation_history = [],
        )

        try:
            sid = make_user_agent_call(phone, str(session.id))
            call_log.twilio_call_sid = sid
            call_log.status          = CallLog.Status.RINGING
            call_log.save()
            session.twilio_call_sid = sid
            session.save()
            return Response({
                'message'   : 'Our agent will call you in a few seconds',
                'session_id': str(session.id),
                'phone'     : phone,
            })
        except Exception as e:
            call_log.status = CallLog.Status.FAILED
            call_log.save()
            return Response({'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────
#  Transfer webhooks
# ─────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class TransferCallWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, transfer_id):
        from twilio.twiml.voice_response import VoiceResponse
        try:
            transfer = TransferRequest.objects.select_related(
                'patient', 'from_hospital', 'to_hospital'
            ).get(pk=transfer_id)
            twiml = build_transfer_twiml(transfer)
        except TransferRequest.DoesNotExist:
            r = VoiceResponse()
            r.say('Transfer request not found. Goodbye.')
            r.hangup()
            twiml = str(r)
        return HttpResponse(twiml, content_type='text/xml')

@method_decorator(csrf_exempt, name='dispatch')
class TransferAlertWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, transfer_id):
        from twilio.twiml.voice_response import VoiceResponse
        try:
            transfer = TransferRequest.objects.select_related(
                'patient', 'from_hospital', 'to_hospital'
            ).get(pk=transfer_id)
            twiml = build_transfer_alert_twiml(transfer)
        except TransferRequest.DoesNotExist:
            r = VoiceResponse()
            r.say('Transfer request not found. Goodbye.')
            r.hangup()
            twiml = str(r)
        return HttpResponse(twiml, content_type='text/xml')


@method_decorator(csrf_exempt, name='dispatch')
class TransferAcknowledgeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, transfer_id):
        from twilio.twiml.voice_response import VoiceResponse
        from .services import VOICE_EN, VOICE_HI, LANG_EN, LANG_HI
        digit = request.POST.get('Digits', '')

        response = VoiceResponse()
        if digit == '1':
            response.say(
                'Thank you. Transfer acknowledged. Please prepare to receive the patient. Goodbye.',
                voice=VOICE_EN, language=LANG_EN
            )
            response.say(
                'धन्यवाद। ट्रांसफर की पुष्टि हुई। मरीज को प्राप्त करने के लिए तैयार रहें।',
                voice=VOICE_HI, language=LANG_HI
            )
            CallLog.objects.filter(
                transfer_request_id=transfer_id
            ).update(status=CallLog.Status.COMPLETED)
        else:
            response.say('No valid input received. Goodbye.', voice=VOICE_EN)
        response.hangup()
        return HttpResponse(str(response), content_type='text/xml')


# ─────────────────────────────────────────────────────────────
#  Agent webhooks — KEY FIXES HERE
# ─────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class IncomingCallView(APIView):
    """Handles direct calls to your Twilio number."""
    permission_classes = [AllowAny]

    def post(self, request):
        from twilio.twiml.voice_response import VoiceResponse
        twilio_call_sid = request.POST.get('CallSid', '')
        from_number     = request.POST.get('From', '')

        call_log = CallLog.objects.create(
            call_type       = CallLog.CallType.USER_AGENT,
            to_number       = from_number,
            twilio_call_sid = twilio_call_sid,
            status          = CallLog.Status.IN_PROGRESS,
        )
        session = CallSession.objects.create(
            call_log             = call_log,
            twilio_call_sid      = twilio_call_sid,
            conversation_history = [],
        )

        response = VoiceResponse()
        response.redirect(
            f'{settings.BASE_WEBHOOK_URL}/api/calls/webhook/agent/greet/{str(session.id)}/',
            method='POST'
        )
        return HttpResponse(str(response), content_type='text/xml')


@method_decorator(csrf_exempt, name='dispatch')
class AgentGreetWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        # KEY FIX — update twilio_call_sid when call connects
        call_sid = request.POST.get('CallSid', '')

        try:
            session = CallSession.objects.get(id=session_id)
            if call_sid and not session.twilio_call_sid:
                session.twilio_call_sid = call_sid
                session.save(update_fields=['twilio_call_sid'])
        except CallSession.DoesNotExist:
            from twilio.twiml.voice_response import VoiceResponse
            r = VoiceResponse()
            r.say('Session error. Please try again.')
            r.hangup()
            return HttpResponse(str(r), content_type='text/xml')

        twiml = build_language_select_twiml(session_id)
        return HttpResponse(twiml, content_type='text/xml')


@method_decorator(csrf_exempt, name='dispatch')
class AgentLanguageWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        # support ?default=1 redirect when no key was pressed
        digit   = request.POST.get('Digits') or request.GET.get('default', '1')
        language = 'hi' if digit == '2' else 'en'

        try:
            session          = CallSession.objects.get(id=session_id)
            session.language = language
            session.save(update_fields=['language'])
        except CallSession.DoesNotExist:
            from twilio.twiml.voice_response import VoiceResponse
            r = VoiceResponse()
            r.say('Session not found. Goodbye.')
            r.hangup()
            return HttpResponse(str(r), content_type='text/xml')

        # apps/calls/views.py — inside AgentLanguageWebhookView.post()
# replace the greeting block:

        from .agent import get_city_hospital_names, AGENT_NAME
        city = session.user_city

        if language == 'hi':
            if city:
                names = get_city_hospital_names(city)
                if names:
                    name_list = ', '.join([n.split('(')[0].strip() for n in names[:4]])
                    greeting = (
                        f'Namaste! Main {AGENT_NAME} hoon, '
                        f'aapki Healthcare Assistant. '
                        f'{city} mein ye hospitals available hain: {name_list}. '
                        f'Aap kisi ek ke baare mein jaanna chahte hain?'
                    )
                else:
                    greeting = (
                        f'Namaste! Main {AGENT_NAME} hoon, '
                        f'aapki Healthcare Assistant. '
                        f'Aap kis shahar mein hospital dhundh rahe hain?'
                    )
            else:
                greeting = (
                    f'Namaste! Main {AGENT_NAME} hoon, '
                    f'aapki personal Healthcare Assistant. '
                    f'Bataiye, aap kis shahar mein hain '
                    f'aur aapko kaise madad chahiye?'
                )
        else:
            if city:
                names = get_city_hospital_names(city)
                if names:
                    name_list = ', '.join([n.split('(')[0].strip() for n in names[:4]])
                    greeting = (
                        f'Hello! I\'m {AGENT_NAME}, '
                        f'your Healthcare Assistant. '
                        f'I can see hospitals in {city} for you — '
                        f'there\'s {name_list}. '
                        f'Which one would you like to know more about?'
                    )
                else:
                    greeting = (
                        f'Hello! I\'m {AGENT_NAME}, '
                        f'your Healthcare Assistant. '
                        f'Which city are you looking for hospitals in?'
                    )
            else:
                greeting = (
                    f'Hello! I\'m {AGENT_NAME}, '
                    f'your personal Healthcare Assistant. '
                    f'Tell me, which city are you in '
                    f'and how can I help you today?'
                )

        session.conversation_history = [{'role': 'assistant', 'content': greeting}]
        session.save(update_fields=['conversation_history'])

        twiml = build_agent_listen_twiml(session_id, greeting, language)
        return HttpResponse(twiml, content_type='text/xml')

# 2. Replace AgentProcessWebhookView.post() completely:

@method_decorator(csrf_exempt, name='dispatch')
class AgentProcessWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, session_id):
        user_speech = request.POST.get('SpeechResult', '').strip()
        confidence  = float(request.POST.get('Confidence', 0))
        is_retry    = request.GET.get('retry') == '1'

        try:
            session = CallSession.objects.get(id=session_id)
        except CallSession.DoesNotExist:
            from twilio.twiml.voice_response import VoiceResponse
            r = VoiceResponse()
            r.say('Session expired. Goodbye.')
            r.hangup()
            return HttpResponse(str(r), content_type='text/xml')

        language = session.language or 'en'
        meta     = session.meta_data or {}

        # ── no speech ─────────────────────────────────────────
        if not user_speech or confidence < 0.3:
            if is_retry:
                twiml = build_agent_end_twiml(language)
            else:
                prompt = ('Main aapki awaaz nahi sun saka. Kripya dobara bolein.'
                          if language == 'hi' else
                          "I didn't catch that. Please speak clearly.")
                twiml = build_agent_listen_twiml(session_id, prompt, language)
            return HttpResponse(twiml, content_type='text/xml')

        # ── language detection ────────────────────────────────
        if not session.language:
            language = detect_language_from_speech(user_speech)
            session.language = language

        # ── city detection ────────────────────────────────────
        if not session.user_city:
            detected = detect_city_from_text(user_speech)
            if detected:
                session.user_city = detected

        from .agent import (
            detect_intent, extract_filters_from_speech,
            extract_hospital_name_from_speech, build_sms_text,
        )

        intent  = detect_intent(user_speech, awaiting_sms=False)
        filters = extract_filters_from_speech(user_speech)

        # ── exit words ────────────────────────────────────────
        exit_words = ['bye', 'goodbye', 'thank you', 'thanks',
                      "that's all", 'dhanyawad', 'shukriya',
                      'धन्यवाद', 'बाय', 'ठीक है', 'बस', 'शुक्रिया']
        is_exit = any(w in user_speech.lower() for w in exit_words)

        # ── SMS send — only when user explicitly asks ─────────
        if intent == 'sms_confirm':
            to_number     = session.call_log.to_number
            last_filters  = meta.get('last_filters', {})
            last_hospital = meta.get('last_hospital_name')
            last_intent   = meta.get('last_intent', 'general')

            sms_text = build_sms_text(
                city          = session.user_city or '',
                intent        = last_intent,
                filters       = last_filters,
                hospital_name = last_hospital,
                language      = language,
            )

            success, sms_error = send_sms(to_number, sms_text)
            session.resolved = True
            session.save()

            if success:
                reply = ('Bilkul! Details aapke number par SMS kar di gayi hain. Apna khayal rakhein!'
                        if language == 'hi' else
                        'Done! I have sent the hospital details to your phone. Take care!')
            else:
                print(f'SMS Error detail: {sms_error}')
                reply = ('Ek choti si takniki dikkat aayi SMS mein. '
                        'Aap seedha hospital ko call kar sakte hain. Apna khayal rakhein!'
                        if language == 'hi' else
                        'I ran into a small issue sending the SMS. '
                        'You can call the hospital directly. Take care!')

            from twilio.twiml.voice_response import VoiceResponse
            from .services import VOICE_HI, VOICE_EN, LANG_HI, LANG_EN
            response = VoiceResponse()
            response.say(
                reply,
                voice    = VOICE_HI if language == 'hi' else VOICE_EN,
                language = LANG_HI  if language == 'hi' else LANG_EN,
            )
            response.hangup()
            return HttpResponse(str(response), content_type='text/xml')

        # ── exit without SMS ──────────────────────────────────
        if is_exit and len(session.conversation_history) > 2:
            session.resolved  = True
            session.meta_data = meta
            session.save()
            twiml = build_agent_end_twiml(language)
            return HttpResponse(twiml, content_type='text/xml')

        # ── track last context for SMS ────────────────────────
        if session.user_city:
            h_name = extract_hospital_name_from_speech(
                user_speech, session.user_city
            )
            if h_name:
                meta['last_hospital_name'] = h_name

        meta['last_filters'] = filters
        meta['last_intent']  = intent

        # ── call Groq — clean response, no SMS mention ────────
        history = session.conversation_history or []
        history.append({'role': 'user', 'content': user_speech})

        agent_response = ask_groq(
            conversation_history = history,
            language             = language,
            city                 = session.user_city,
            filters              = filters,
            intent               = intent,
        )

        # ── save CLEAN response to history (no SMS tip) ───────
        history.append({'role': 'assistant', 'content': agent_response})
        if len(history) > 12:
            history = history[-12:]

        session.conversation_history = history
        session.meta_data            = meta
        session.save()

        # ── add SMS tip ONCE — appended AFTER saving history ──
        # This means it is spoken to user but never stored
        # so Groq never sees it and never repeats it
        spoken_response = agent_response
        if (
            not meta.get('end_note_shown') and
            len(history) >= 4 and
            session.user_city
        ):
            meta['end_note_shown'] = True
            session.meta_data = meta
            session.save()

            tip = ('Aap yeh jaankari message par bhi pa sakte hain — bas kahein message bhejo.'
                   if language == 'hi' else
                   'You can also receive this on SMS — just say send message.')

            spoken_response = f'{agent_response} {tip}'

        twiml = build_agent_listen_twiml(session_id, spoken_response, language)
        return HttpResponse(twiml, content_type='text/xml')
@method_decorator(csrf_exempt, name='dispatch')
class CallStatusWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        call_sid      = request.POST.get('CallSid', '')
        call_status   = request.POST.get('CallStatus', '')
        call_duration = request.POST.get('CallDuration', 0)

        status_map = {
            'completed'  : CallLog.Status.COMPLETED,
            'failed'     : CallLog.Status.FAILED,
            'no-answer'  : CallLog.Status.NO_ANSWER,
            'busy'       : CallLog.Status.FAILED,
            'canceled'   : CallLog.Status.FAILED,
            'in-progress': CallLog.Status.IN_PROGRESS,
        }

        CallLog.objects.filter(twilio_call_sid=call_sid).update(
            status       = status_map.get(call_status, CallLog.Status.FAILED),
            duration_sec = int(call_duration) if call_duration else None,
        )
        return HttpResponse('OK', content_type='text/plain')