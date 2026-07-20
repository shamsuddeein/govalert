import os
import sys
import django

sys.path.insert(0, '/home/deen/GovAlert')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.agencies.models import Portal, Agency
from apps.monitor.models import Snapshot
from apps.api.serializers import AgencyDetailSerializer, AgencyListSerializer

portals = Portal.objects.select_related('agency').all()

print(f"Total portals in DB: {portals.count()}")
print("=" * 100)
print(f"{'Agency':<10} {'Portal Name':<28} {'Snaps':<8} {'Speed (ms)':<12} {'Health':<12} {'Last 10 Status Codes'}")
print("-" * 100)

for p in portals[:20]:
    snaps = Snapshot.objects.filter(portal=p).order_by('-created_at')
    snap_count = snaps.count()
    avg_speed = p.response_time_ms
    last_10 = list(snaps.values_list('status_code', flat=True)[:10])
    print(f"{p.agency.acronym:<10} {p.name[:26]:<28} {snap_count:<8} {str(avg_speed):<12} {p.health_status:<12} {last_10}")

print("=" * 100)

# Check serializer output for AgencyDetailView
agencies = Agency.objects.filter(is_active=True)[:5]
for a in agencies:
    serializer = AgencyDetailSerializer(a)
    data = serializer.data
    print(f"\nAgency Serializer Output for {a.acronym} ({a.name}):")
    print(f"  uptime_percent: {data.get('uptime_percent')}")
    print(f"  response_time_ms: {data.get('response_time_ms')}")
    print(f"  last_10_checks: {data.get('last_10_checks')}")
    print(f"  last_10_checks type: {type(data.get('last_10_checks'))}")
    print(f"  total_checks: {data.get('total_checks')}")
