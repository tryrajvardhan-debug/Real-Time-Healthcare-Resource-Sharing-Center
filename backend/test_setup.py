from apps.authentication.models import User
from apps.hospitals.models import Hospital
from rest_framework_simplejwt.tokens import RefreshToken

# Check if hospitals exist
hospitals = Hospital.objects.filter(city='Indore')
print(f"✓ Total hospitals in Indore: {hospitals.count()}")

if hospitals.count() == 0:
    print("❌ No hospitals found. Seed failed.")
else:
    hospital = hospitals.first()
    print(f"✓ First hospital: {hospital.name}")
    
    # Delete existing test user if exists
    User.objects.filter(email='reception@hospital.com').delete()
    
    # Create reception user
    reception = User.objects.create_user(
        email='reception@hospital.com',
        password='Reception@123',
        full_name='Test Reception',
        role='reception',
        phone='9876543210',
        hospital=hospital
    )
    print(f"✓ Created reception user: {reception.email}")
    
    # Test token generation
    refresh = RefreshToken.for_user(reception)
    access = str(refresh.access_token)
    refresh_str = str(refresh)
    
    print(f"\n✓ Access Token generated (first 50 chars): {access[:50]}...")
    print(f"✓ Refresh Token generated (first 50 chars): {refresh_str[:50]}...")
    print(f"\n✓ User is_active: {reception.is_active}")
    print(f"✓ User role: {reception.role}")
    print(f"✓ User hospital: {reception.hospital.name}")
    
    print("\n✅ All setup complete! User ready for login.")
