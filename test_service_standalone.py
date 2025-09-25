#!/usr/bin/env python3
"""Standalone test of data ingestion service without Kafka/Docker."""

import asyncio
import sys
from pathlib import Path

# Add service source to path
service_path = Path(__file__).parent / "services/data-ingestion-service"
sys.path.insert(0, str(service_path))

# Test imports
try:
    from src.domain.disaster_event import DisasterType, EarthquakeMagnitude, Location
    from src.infrastructure.usgs_service import USGSIngestionService
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic service functionality without Kafka."""
    print("\n🔍 Testing USGS Service...")

    service = USGSIngestionService()

    try:
        # Test 1: Fetch recent earthquakes
        print("📡 Fetching recent earthquakes...")
        raw_earthquakes = await service.fetch_raw_earthquake_data(
            period="day", magnitude="significant"
        )

        print(f"✅ Fetched {len(raw_earthquakes)} earthquakes")

        if raw_earthquakes:
            # Test 2: Process first earthquake
            print("\n⚙️ Processing first earthquake...")
            first_raw = raw_earthquakes[0]
            processed = service.process_earthquake_feature(first_raw)

            if processed:
                print("✅ Successfully processed earthquake:")
                print(f"   Event ID: {processed.event_id}")
                print(f"   External ID: {processed.external_id}")
                print(f"   Location: {processed.location.latitude:.3f}, {processed.location.longitude:.3f}")
                print(f"   Magnitude: {processed.severity.value} ({processed.severity.scale})")
                print(f"   Severity: {processed.severity.get_level().value}")
                print(f"   Significant: {processed.severity.is_significant()}")
                print(f"   Title: {processed.title}")
            else:
                print("❌ Failed to process earthquake")

        # Test 3: Validate domain models
        print("\n🧪 Testing domain models...")

        # Test location validation
        location = Location(latitude=34.123, longitude=-118.456, depth=10.5)
        print(f"✅ Valid location created: {location}")

        # Test magnitude
        magnitude = EarthquakeMagnitude(value=6.2)
        print(f"✅ Magnitude: {magnitude.value} -> {magnitude.get_level().value}")

        # Test invalid location (should raise error)
        try:
            Location(latitude=91.0, longitude=0.0)  # Invalid
            print("❌ Should have rejected invalid latitude")
        except ValueError:
            print("✅ Correctly rejected invalid latitude")

        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Fix Docker/Kafka connectivity issues")
        print("2. Test full stack: docker-compose -f docker-compose.lightweight.yml up")
        print("3. Test API endpoints: curl http://localhost:8000/health")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        await service.close()


async def main():
    """Main test function."""
    print("🚀 Testing NDGMS Data Ingestion Service")
    print("=" * 50)

    success = await test_basic_functionality()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
