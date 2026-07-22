"""
Load Nigerian government agency recruitment portals into GovAlert.
Reads from data/nigeria_portals.json for easy maintenance.

Usage:
    python manage.py load_ng_portals              # Load all portals
    python manage.py load_ng_portals --dry-run    # Preview changes
"""
import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from apps.agencies.models import Agency, Portal, PortalPriority


def get_poll_interval(priority: str) -> int:
    """Convert priority to poll_interval in seconds."""
    intervals = {
        PortalPriority.HIGH: 300,     # 5 minutes
        PortalPriority.MEDIUM: 1200,  # 20 minutes
        PortalPriority.LOW: 3600,     # 60 minutes
    }
    return intervals.get(priority, 900)


def load_portal_data() -> list:
    """Load portals from data/nigeria_portals.json."""
    data_path = os.path.join(settings.BASE_DIR, 'data', 'nigeria_portals.json')
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Portal data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        return json.load(f)
    {
        'name': 'Nigeria Police Force Recruitment',
        'acronym': 'NPF',
        'url': 'https://recruitment.psc.gov.ng',
    },
    {
        'name': 'Police Service Commission',
        'acronym': 'PSC',
        'url': 'https://psc.gov.ng',
    },
    {
        'name': 'Nigeria Immigration Service',
        'acronym': 'NIS',
        'url': 'https://immigration.gov.ng',
    },
    {
        'name': 'Nigeria Customs Service',
        'acronym': 'NCS',
        'url': 'https://customs.gov.ng',
    },
    {
        'name': 'Nigeria Security and Civil Defence Corps',
        'acronym': 'NSCDC',
        'url': 'https://cdcfib.career',
    },
    {
        'name': 'Federal Fire Service',
        'acronym': 'FFS',
        'url': 'https://cdcfib.career',
    },
    {
        'name': 'Nigerian Correctional Service',
        'acronym': 'NCoS',
        'url': 'https://cdcfib.career',
    },
    {
        'name': 'Civil Defence, Correctional, Fire and Immigration Board',
        'acronym': 'CDCFIB',
        'url': 'https://cdcfib.gov.ng',
    },
    {
        'name': 'Federal Road Safety Corps',
        'acronym': 'FRSC',
        'url': 'https://frsc.gov.ng',
    },
    {
        'name': 'Nigerian Army',
        'acronym': 'Army',
        'url': 'https://recruitment.army.mil.ng',
    },
    {
        'name': 'Nigerian Navy',
        'acronym': 'Navy',
        'url': 'https://joinnigeriannavy.com',
    },
    {
        'name': 'Nigerian Air Force',
        'acronym': 'NAF',
        'url': 'https://nafrecruitment.airforce.mil.ng',
    },
    {
        'name': 'Nigerian Defence Academy',
        'acronym': 'NDA',
        'url': 'https://nda.edu.ng',
    },
    {
        'name': 'Department of State Services',
        'acronym': 'DSS',
        'url': 'https://dss.gov.ng',
    },
    {
        'name': 'National Drug Law Enforcement Agency',
        'acronym': 'NDLEA',
        'url': 'https://ndlea.gov.ng',
    },
    {
        'name': 'Economic and Financial Crimes Commission',
        'acronym': 'EFCC',
        'url': 'https://efcc.gov.ng',
    },
    {
        'name': 'Independent Corrupt Practices Commission',
        'acronym': 'ICPC',
        'url': 'https://icpc.gov.ng',
    },
    {
        'name': 'Independent National Electoral Commission',
        'acronym': 'INEC',
        'url': 'https://recruitment.inecnigeria.org',
    },
    {
        'name': 'Nigerian National Petroleum Company',
        'acronym': 'NNPC',
        'url': 'https://careers.nnpcgroup.com',
    },
    {
        'name': 'Central Bank of Nigeria',
        'acronym': 'CBN',
        'url': 'https://cbn.gov.ng',
    },
    {
        'name': 'Federal Inland Revenue Service',
        'acronym': 'FIRS',
        'url': 'https://firs.gov.ng',
    },
    {
        'name': 'Nigerian Ports Authority',
        'acronym': 'NPA',
        'url': 'https://nigerianports.gov.ng',
    },
    {
        'name': 'Nigerian Maritime Administration and Safety Agency',
        'acronym': 'NIMASA',
        'url': 'https://nimasa.gov.ng',
    },
    {
        'name': 'Nigerian Railway Corporation',
        'acronym': 'NRC',
        'url': 'https://nrc.gov.ng',
    },
    {
        'name': 'Nigerian Communications Commission',
        'acronym': 'NCC',
        'url': 'https://ncc.gov.ng',
    },
    {
        'name': 'National Information Technology Development Agency',
        'acronym': 'NITDA',
        'url': 'https://nitda.gov.ng',
    },
    {
        'name': 'Joint Admissions and Matriculation Board',
        'acronym': 'JAMB',
        'url': 'https://jamb.gov.ng',
    },
    {
        'name': 'National Agency for Food and Drug Administration and Control',
        'acronym': 'NAFDAC',
        'url': 'https://nafdac.gov.ng',
    },
    {
        'name': 'National Identity Management Commission',
        'acronym': 'NIMC',
        'url': 'https://nimc.gov.ng',
    },
    {
        'name': 'Universal Basic Education Commission',
        'acronym': 'UBEC',
        'url': 'https://ubec.gov.ng',
    },
    {
        'name': 'Teachers Registration Council of Nigeria',
        'acronym': 'TRCN',
        'url': 'https://trcn.gov.ng',
    },
    {
        'name': 'National Health Insurance Authority',
        'acronym': 'NHIA',
        'url': 'https://nhia.gov.ng',
    },
    {
        'name': 'Federal Ministry of Health',
        'acronym': 'FMH',
        'url': 'https://health.gov.ng',
    },
    {
        'name': 'Federal Ministry of Education',
        'acronym': 'FME',
        'url': 'https://education.gov.ng',
    },
    {
        'name': 'Federal Ministry of Interior',
        'acronym': 'FMI',
        'url': 'https://interior.gov.ng',
    },
    {
        'name': 'Federal Ministry of Defence',
        'acronym': 'FMD',
        'url': 'https://defence.gov.ng',
    },
    {
        'name': 'Federal Ministry of Finance',
        'acronym': 'FMF',
        'url': 'https://finance.gov.ng',
    },
    {
        'name': 'Federal Ministry of Works',
        'acronym': 'FMW',
        'url': 'https://works.gov.ng',
    },
    {
        'name': 'Federal Ministry of Agriculture',
        'acronym': 'FMA',
        'url': 'https://agriculture.gov.ng',
    },


class Command(BaseCommand):
    help = 'Load Nigerian government agency recruitment portals from data/nigeria_portals.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        try:
            portal_data = load_portal_data()
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for data in portal_data:
            agency_name = data['name']
            agency_acronym = data['acronym']
            portal_url = data['url']
            priority = data.get('priority', PortalPriority.MEDIUM)
            scrape_method = data.get('scrape_method', 'REQUESTS')
            tags = data.get('tags', [])
            country = data.get('country', 'NG')
            poll_interval = get_poll_interval(priority)

            # Create or get agency by acronym or name (robust to discrepancies)
            agency = Agency.objects.filter(acronym=agency_acronym).first()
            if not agency:
                agency = Agency.objects.filter(name=agency_name).first()
            
            if not agency:
                agency = Agency.objects.create(
                    acronym=agency_acronym,
                    name=agency_name
                )
            else:
                updated_fields = []
                if agency.acronym != agency_acronym:
                    agency.acronym = agency_acronym
                    updated_fields.append('acronym')
                if agency.name != agency_name:
                    agency.name = agency_name
                    updated_fields.append('name')
                if updated_fields:
                    agency.save(update_fields=updated_fields)

            # Create or update portal safely without crashing on existing duplicates
            # First try exact URL match
            existing_portals = list(Portal.objects.filter(agency=agency, url=portal_url))
            if not existing_portals:
                existing_portals = list(Portal.objects.filter(url=portal_url))

            if not existing_portals:
                # URL may have changed — look up by agency and update the stale URL
                existing_portals = list(Portal.objects.filter(agency=agency))

            if existing_portals:
                portal = existing_portals[0]
                portal_created = False
                # If there are duplicate portal records for this agency, clean up extra rows
                if len(existing_portals) > 1:
                    for dup in existing_portals[1:]:
                        dup.delete()
                # Update the URL if it has changed (e.g. INEC portal URL migration)
                if portal.url != portal_url:
                    if not dry_run:
                        portal.url = portal_url
                        portal.save(update_fields=['url'])
                    self.stdout.write(
                        self.style.WARNING(
                            f"URL updated: {agency_acronym:8} | {portal.url} → {portal_url}"
                        )
                    )
            else:
                portal = Portal.objects.create(
                    agency=agency,
                    url=portal_url,
                    name=agency_name,
                    priority=priority,
                    scrape_method=scrape_method,
                    tags=tags,
                    country=country,
                    poll_interval=poll_interval,
                    is_active=True,
                )
                portal_created = True

            if portal_created:
                created_count += 1
                action = "Created" if not dry_run else "[DRY-RUN] Would create"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{action}: {agency_acronym:8} | {priority:8} | {poll_interval:5}s | {portal_url[:40]}"
                    )
                )
            else:
                # Update existing portal with new metadata
                updated = False
                if portal.priority != priority:
                    portal.priority = priority
                    portal.poll_interval = poll_interval
                    updated = True
                if portal.tags != tags:
                    portal.tags = tags
                    updated = True
                
                if updated:
                    if not dry_run:
                        portal.save(update_fields=['priority', 'poll_interval', 'tags'])
                    updated_count += 1
                    action = "Updated" if not dry_run else "[DRY-RUN] Would update"
                    self.stdout.write(
                        self.style.WARNING(
                            f"{action}: {agency_acronym:8} | {priority:8} | {poll_interval:5}s"
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped:  {agency_acronym:8} | {priority:8} | {poll_interval:5}s (no changes)"
                        )
                    )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY-RUN] Would create {created_count}, update {updated_count}, "
                    f"skip {skipped_count} portals"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Created {created_count}, updated {updated_count}, "
                    f"skipped {skipped_count} portals"
                )
            )
