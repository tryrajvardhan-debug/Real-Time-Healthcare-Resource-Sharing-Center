# apps/ambulances/views.py
from django.utils import timezone
from django.db.models import Q, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.notify import notify_driver_new_request

from core.permissions import (
    IsReception, IsAmbulanceDriver,
    IsStaffMember, IsAdminUser, IsSameHospitalStaff
)
from apps.patients.models import Patient
from .models import Ambulance, AmbulanceRequest
from .serializers import (
    AmbulanceSerializer, AmbulancePublicSerializer,
    AmbulanceStatusUpdateSerializer, LocationUpdateSerializer,
    AmbulanceRequestSerializer, BookAmbulanceSerializer,
    RateAmbulanceSerializer,
)
from .cache import (
    get_available_ambulances_in_city,
    invalidate_city_ambulances,
    set_ambulance_status, get_ambulance_status,
    update_driver_location, get_driver_location,
    set_active_request, get_active_request, clear_active_request,
)


# ─────────────────────────────────────────────────────────────
#  Public — patient portal
# ─────────────────────────────────────────────────────────────

class AvailableAmbulancesView(APIView):
    """
    GET /api/ambulances/available/?city=Bhopal&type=basic
    Patient portal — shows available ambulances in a city.
    Served from Redis cache.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        city          = request.query_params.get('city', '').strip()
        ambulance_type = request.query_params.get('type', '').strip()

        if not city:
            return Response(
                {'error': 'city param is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = get_available_ambulances_in_city(city)

        # filter by type in memory — avoids DB hit
        if ambulance_type:
            data = [a for a in data if a['ambulance_type'] == ambulance_type]

        return Response({
            'city'       : city,
            'count'      : len(data),
            'ambulances' : data,
        })



class BookAmbulanceView(APIView):
    """
    POST /api/ambulances/book/
    Patient books an ambulance — no login needed.
    System auto-assigns nearest available ambulance.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BookAmbulanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # find nearest available ambulance in the city
        ambulance = Ambulance.objects.filter(
            city__iexact=data['pickup_city'],
            ambulance_type=data['ambulance_type'],
            status=Ambulance.Status.AVAILABLE,
            is_active=True
        ).order_by('service_rating').last()   # highest rated first

        if not ambulance:
            return Response(
                {
                    'error'  : 'No ambulances available in your area right now',
                    'city'   : data['pickup_city'],
                    'type'   : data['ambulance_type'],
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # get or create patient record
        patient = None
        if data.get('patient_id'):
            try:
                patient = Patient.objects.get(pk=data['patient_id'])
            except Patient.DoesNotExist:
                pass

        if not patient:
            patient = Patient.objects.create(
                full_name=data['requester_name'],
                phone=data['requester_phone'],
            )

        # create the request
        amb_request = AmbulanceRequest.objects.create(
            ambulance            = ambulance,
            patient              = patient,
            destination_hospital_id = data.get('destination_hospital'),
            pickup_address       = data['pickup_address'],
            pickup_latitude      = data.get('pickup_latitude'),
            pickup_longitude     = data.get('pickup_longitude'),
            pickup_city          = data['pickup_city'],
            ambulance_type       = data['ambulance_type'],
            requester_name       = data['requester_name'],
            requester_phone      = data['requester_phone'],
            notes                = data.get('notes', ''),
            source               = AmbulanceRequest.RequestSource.PATIENT,
        )

        # mark ambulance as on trip
        ambulance.status = Ambulance.Status.ON_TRIP
        ambulance.save(update_fields=['status', 'updated_at'])

        # update Redis
        set_ambulance_status(str(ambulance.id), Ambulance.Status.ON_TRIP)
        set_active_request(str(ambulance.id), str(amb_request.id))
        invalidate_city_ambulances(ambulance.city)

        try:
                notify_driver_new_request(str(ambulance.id), amb_request)
        except Exception:
            # never let notification failure break the booking
            # driver can still see the request on next dashboard poll
            pass

        

        return Response({
            'message'     : 'Ambulance booked successfully',
            'request_id'  : str(amb_request.id),
            'driver_name' : ambulance.driver_name,
            'driver_phone': ambulance.driver_phone,
            'vehicle'     : ambulance.vehicle_number,
            'eta_note'    : 'Driver will contact you shortly',
        }, status=status.HTTP_201_CREATED)


class TrackAmbulanceView(APIView):
    """
    GET /api/ambulances/track/<request_id>/
    Patient tracks live driver location for their active request.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            amb_request = AmbulanceRequest.objects.select_related(
                'ambulance'
            ).get(pk=pk)
        except AmbulanceRequest.DoesNotExist:
            return Response({'error': 'Request not found'}, status=404)

        location = None
        if amb_request.ambulance:
            location = get_driver_location(str(amb_request.ambulance.id))

        return Response({
            'request_id'  : str(amb_request.id),
            'status'      : amb_request.status,
            'driver_name' : amb_request.ambulance.driver_name if amb_request.ambulance else None,
            'driver_phone': amb_request.ambulance.driver_phone if amb_request.ambulance else None,
            'vehicle'     : amb_request.ambulance.vehicle_number if amb_request.ambulance else None,
            'live_location': location,
        })


class RateAmbulanceView(APIView):
    """
    POST /api/ambulances/rate/<request_id>/
    Patient rates the service after trip is completed.
    Updates the ambulance's average rating.
    """
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            amb_request = AmbulanceRequest.objects.select_related(
                'ambulance'
            ).get(pk=pk, status=AmbulanceRequest.Status.COMPLETED)
        except AmbulanceRequest.DoesNotExist:
            return Response(
                {'error': 'Completed request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = RateAmbulanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amb_request.patient_rating = serializer.validated_data['rating']
        amb_request.save(update_fields=['patient_rating'])

        # recalculate ambulance average rating
        ambulance = amb_request.ambulance
        avg = AmbulanceRequest.objects.filter(
            ambulance=ambulance,
            patient_rating__isnull=False
        ).aggregate(avg=Avg('patient_rating'))['avg']

        ambulance.service_rating = round(avg, 2)
        ambulance.save(update_fields=['service_rating'])

        return Response({'message': 'Thank you for your rating'})


# ─────────────────────────────────────────────────────────────
#  Driver portal — ambulance driver's own views
# ─────────────────────────────────────────────────────────────

class DriverDashboardView(APIView):
    """
    GET /api/ambulances/driver/dashboard/
    Driver sees their ambulance info + active request if any.
    """
    permission_classes = [IsAmbulanceDriver]

    def get(self, request):
        try:
            ambulance = request.user.ambulance
        except Ambulance.DoesNotExist:
            return Response(
                {'error': 'No ambulance assigned to your account'},
                status=status.HTTP_404_NOT_FOUND
            )

        active_request_id = get_active_request(str(ambulance.id))
        active_request    = None

        if active_request_id:
            try:
                active_request = AmbulanceRequest.objects.select_related(
                    'patient', 'destination_hospital'
                ).get(pk=active_request_id)
            except AmbulanceRequest.DoesNotExist:
                pass

        return Response({
            'ambulance'     : AmbulanceSerializer(ambulance).data,
            'active_request': AmbulanceRequestSerializer(active_request).data if active_request else None,
        })


class DriverSetAvailabilityView(APIView):
    """
    PATCH /api/ambulances/driver/availability/
    Driver marks themselves available or goes offline.
    Body: { "status": "available" | "inactive" }
    """
    permission_classes = [IsAmbulanceDriver]

    def patch(self, request):
        try:
            ambulance = request.user.ambulance
        except Ambulance.DoesNotExist:
            return Response({'error': 'No ambulance assigned'}, status=404)

        new_status = request.data.get('status')
        allowed    = [Ambulance.Status.AVAILABLE, Ambulance.Status.INACTIVE]

        if new_status not in allowed:
            return Response(
                {'error': f'Status must be one of {allowed}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # can't go available while on a trip
        if ambulance.status == Ambulance.Status.ON_TRIP:
            return Response(
                {'error': 'Cannot change status while on a trip'},
                status=status.HTTP_400_BAD_REQUEST
            )

        ambulance.status = new_status
        ambulance.save(update_fields=['status', 'updated_at'])

        set_ambulance_status(str(ambulance.id), new_status)
        invalidate_city_ambulances(ambulance.city)

        return Response({'status': new_status, 'message': 'Availability updated'})


class DriverUpdateLocationView(APIView):
    """
    POST /api/ambulances/driver/location/
    Driver app sends GPS every ~10 seconds while on a trip.
    Stored in Redis only — not persisted to DB.
    Body: { "latitude": 23.2599, "longitude": 77.4126 }
    """
    permission_classes = [IsAmbulanceDriver]

    def post(self, request):
        serializer = LocationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ambulance = request.user.ambulance
        except Ambulance.DoesNotExist:
            return Response({'error': 'No ambulance assigned'}, status=404)

        update_driver_location(
            str(ambulance.id),
            float(serializer.validated_data['latitude']),
            float(serializer.validated_data['longitude']),
        )
        return Response({'message': 'Location updated'})


class DriverTripActionView(APIView):
    """
    POST /api/ambulances/driver/trip/<request_id>/action/
    Driver moves the trip through its lifecycle.

    Actions:
      accept     → ACCEPTED  (driver confirms they're going)
      en_route   → EN_ROUTE  (driver has started moving to patient)
      picked_up  → PICKED_UP (patient is on board)
      complete   → COMPLETED (arrived at hospital)
      cancel     → CANCELLED (driver cannot go)
    """
    permission_classes = [IsAmbulanceDriver]

    VALID_TRANSITIONS = {
        'accept'   : (AmbulanceRequest.Status.PENDING,   AmbulanceRequest.Status.ACCEPTED),
        'en_route' : (AmbulanceRequest.Status.ACCEPTED,  AmbulanceRequest.Status.EN_ROUTE),
        'picked_up': (AmbulanceRequest.Status.EN_ROUTE,  AmbulanceRequest.Status.PICKED_UP),
        'complete' : (AmbulanceRequest.Status.PICKED_UP, AmbulanceRequest.Status.COMPLETED),
        'cancel'   : (None,                               AmbulanceRequest.Status.CANCELLED),
    }

    def post(self, request, pk):
        action = request.data.get('action')

        if action not in self.VALID_TRANSITIONS:
            return Response(
                {'error': f'Invalid action. Choose from: {list(self.VALID_TRANSITIONS.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ambulance   = request.user.ambulance
            amb_request = AmbulanceRequest.objects.select_related(
                'ambulance', 'patient', 'destination_hospital'
            ).get(pk=pk, ambulance=ambulance)
        except (Ambulance.DoesNotExist, AmbulanceRequest.DoesNotExist):
            return Response({'error': 'Request not found'}, status=404)

        required_from, new_status = self.VALID_TRANSITIONS[action]

        # validate current state allows this transition
        if required_from and amb_request.status != required_from:
            return Response(
                {'error': f'Cannot {action} a request in {amb_request.status} state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        # apply the transition
        amb_request.status = new_status

        if action == 'accept':
            amb_request.accepted_at       = now
            amb_request.response_time_sec = int(
                (now - amb_request.requested_at).total_seconds()
            )

        elif action == 'picked_up':
            amb_request.picked_up_at = now

        elif action == 'complete':
            amb_request.completed_at      = now
            amb_request.trip_duration_sec = int(
                (now - amb_request.picked_up_at).total_seconds()
            ) if amb_request.picked_up_at else None

            # free the ambulance
            ambulance.status         = Ambulance.Status.AVAILABLE
            ambulance.trips_completed += 1
            ambulance.save(update_fields=['status', 'trips_completed', 'updated_at'])

            clear_active_request(str(ambulance.id))
            set_ambulance_status(str(ambulance.id), Ambulance.Status.AVAILABLE)
            invalidate_city_ambulances(ambulance.city)

        elif action == 'cancel':
            amb_request.cancellation_reason = request.data.get('reason', '')
            ambulance.status = Ambulance.Status.AVAILABLE
            ambulance.save(update_fields=['status', 'updated_at'])
            clear_active_request(str(ambulance.id))
            set_ambulance_status(str(ambulance.id), Ambulance.Status.AVAILABLE)
            invalidate_city_ambulances(ambulance.city)

        amb_request.save()

        return Response({
            'message'   : f'Trip status updated to {new_status}',
            'request'   : AmbulanceRequestSerializer(amb_request).data,
        })


class DriverTripHistoryView(generics.ListAPIView):
    """
    GET /api/ambulances/driver/trips/
    Driver's completed trip history.
    """
    permission_classes = [IsAmbulanceDriver]
    serializer_class   = AmbulanceRequestSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['status']
    ordering_fields    = ['requested_at', 'completed_at']

    def get_queryset(self):
        return AmbulanceRequest.objects.filter(
            ambulance=self.request.user.ambulance
        ).select_related('patient', 'destination_hospital')


# ─────────────────────────────────────────────────────────────
#  Admin / Reception — management views
# ─────────────────────────────────────────────────────────────

class AmbulanceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/ambulances/manage/   → list all ambulances
    POST /api/ambulances/manage/   → register new ambulance
    """
    serializer_class = AmbulanceSerializer
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['city', 'ambulance_type', 'status', 'is_active']
    search_fields    = ['vehicle_number', 'driver_name', 'driver_phone']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsStaffMember()]
        return [IsAdminUser()]

    def get_queryset(self):
        return Ambulance.objects.select_related(
            'hospital', 'driver'
        ).filter(is_active=True)


class AmbulanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/ambulances/manage/<id>/
    PATCH  /api/ambulances/manage/<id>/
    DELETE /api/ambulances/manage/<id>/
    """
    serializer_class = AmbulanceSerializer
    queryset         = Ambulance.objects.select_related('hospital', 'driver')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsStaffMember()]
        return [IsAdminUser()]

    def perform_update(self, serializer):
        ambulance = serializer.save()
        invalidate_city_ambulances(ambulance.city)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
        invalidate_city_ambulances(instance.city)


class AllRequestsView(generics.ListAPIView):
    """
    GET /api/ambulances/requests/
    Staff sees all ambulance requests with filters.
    """
    permission_classes = [IsStaffMember]
    serializer_class   = AmbulanceRequestSerializer
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['status', 'ambulance_type', 'source', 'pickup_city']
    ordering_fields    = ['requested_at', 'completed_at']

    def get_queryset(self):
        return AmbulanceRequest.objects.select_related(
            'ambulance', 'patient', 'destination_hospital'
        )
    
# apps/ambulances/views.py — add below DriverSetAvailabilityView

class ReceptionAmbulanceStatusView(APIView):
    """
    PATCH /api/ambulances/<id>/status/
    Reception OR driver can update ambulance availability.

    Reception use cases:
      - Mark hospital's ambulance under maintenance
      - Mark it available after service
      - Override driver status if driver is unresponsive

    Driver use cases (same endpoint, same body):
      - Toggle available / inactive when going off shift

    Body: { "status": "available" | "maintenance" | "inactive" }
    """
    def get_permissions(self):
        # both reception staff and driver can call this
        from rest_framework.permissions import IsAuthenticated
        return [IsAuthenticated()]

    def patch(self, request, pk):
        try:
            ambulance = Ambulance.objects.select_related(
                'hospital', 'driver'
            ).get(pk=pk)
        except Ambulance.DoesNotExist:
            return Response(
                {'error': 'Ambulance not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        user     = request.user
        new_status = request.data.get('status')
        reason   = request.data.get('reason', '')

        # ── permission check ──────────────────────────────────
        # reception can only update ambulances at their hospital
        if user.role == 'reception':
            if not user.hospital or str(ambulance.hospital_id) != str(user.hospital_id):
                return Response(
                    {'error': 'You can only update ambulances at your hospital'},
                    status=status.HTTP_403_FORBIDDEN
                )
            allowed_statuses = [
                Ambulance.Status.AVAILABLE,
                Ambulance.Status.MAINTENANCE,
                Ambulance.Status.INACTIVE,
            ]

        # driver can only update their own ambulance
        elif user.role == 'ambulance':
            if not hasattr(user, 'ambulance') or str(user.ambulance.id) != str(pk):
                return Response(
                    {'error': 'You can only update your own ambulance'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # driver cannot put ambulance in maintenance (that's reception's job)
            allowed_statuses = [
                Ambulance.Status.AVAILABLE,
                Ambulance.Status.INACTIVE,
            ]

        # admin can update any ambulance to any status
        elif user.role == 'admin':
            allowed_statuses = [s.value for s in Ambulance.Status]

        else:
            return Response(
                {'error': 'You do not have permission to update ambulance status'},
                status=status.HTTP_403_FORBIDDEN
            )

        # ── validate status ───────────────────────────────────
        if new_status not in allowed_statuses:
            return Response(
                {
                    'error'  : f'Invalid status for your role. Allowed: {allowed_statuses}',
                    'current': ambulance.status,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ── block status change while on trip ─────────────────
        if ambulance.status == Ambulance.Status.ON_TRIP and new_status != Ambulance.Status.ON_TRIP:
            return Response(
                {'error': 'Cannot change status while ambulance is on a trip'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status         = ambulance.status
        ambulance.status   = new_status
        ambulance.save(update_fields=['status', 'updated_at'])

        # update Redis
        set_ambulance_status(str(ambulance.id), new_status)
        invalidate_city_ambulances(ambulance.city)

        return Response({
            'message'    : f'Ambulance status updated to {new_status}',
            'ambulance'  : str(ambulance.id),
            'vehicle'    : ambulance.vehicle_number,
            'old_status' : old_status,
            'new_status' : new_status,
            'updated_by' : user.full_name,
            'role'       : user.role,
        })
    
