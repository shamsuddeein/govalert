"""
reconcile_agency_data — Idempotent management command to reconcile all Agency and Portal records with the canonical source of truth.
"""
from django.core.management.base import BaseCommand
from apps.agencies.models import Agency, Portal
from apps.alerts.models import Alert


CANONICAL_AGENCIES = {
    # SECURITY
    'Army': {'category': 'SECURITY', 'domain': 'army.mil.ng', 'name': 'Nigerian Army'},
    'CDCFIB': {'category': 'SECURITY', 'domain': 'cdcfib.gov.ng', 'name': 'Civil Defence, Correctional, Fire and Immigration Board'},
    'DSS': {'category': 'SECURITY', 'domain': 'dss.gov.ng', 'name': 'Department of State Services'},
    'FFS': {'category': 'SECURITY', 'domain': 'fedfire.gov.ng', 'name': 'Federal Fire Service'},
    'NAF': {'category': 'SECURITY', 'domain': 'airforce.mil.ng', 'name': 'Nigerian Air Force'},
    'NCoS': {'category': 'SECURITY', 'domain': 'corrections.gov.ng', 'name': 'Nigerian Correctional Service'},
    'NDA': {'category': 'SECURITY', 'domain': 'nda.edu.ng', 'name': 'Nigerian Defence Academy'},
    'NIS': {'category': 'SECURITY', 'domain': 'immigration.gov.ng', 'name': 'Nigeria Immigration Service'},
    'NPF': {'category': 'SECURITY', 'domain': 'npf.gov.ng', 'name': 'Nigeria Police Force'},
    'NSCDC': {'category': 'SECURITY', 'domain': 'nscdc.gov.ng', 'name': 'Nigeria Security and Civil Defence Corps'},
    'Navy': {'category': 'SECURITY', 'domain': 'navy.mil.ng', 'name': 'Nigerian Navy'},

    # FINANCE
    'EFCC': {'category': 'FINANCE', 'domain': 'efcc.gov.ng', 'name': 'Economic and Financial Crimes Commission'},
    'ICPC': {'category': 'FINANCE', 'domain': 'icpc.gov.ng', 'name': 'Independent Corrupt Practices Commission'},
    'CBN': {'category': 'FINANCE', 'domain': 'cbn.gov.ng', 'name': 'Central Bank of Nigeria'},
    'FIRS': {'category': 'FINANCE', 'domain': 'firs.gov.ng', 'name': 'Federal Inland Revenue Service'},
    'NCS': {'category': 'FINANCE', 'domain': 'customs.gov.ng', 'name': 'Nigeria Customs Service'},

    # UTILITIES
    'NNPC': {'category': 'UTILITIES', 'domain': 'nnpcgroup.com', 'name': 'Nigerian National Petroleum Corporation'},
    'NUPRC': {'category': 'UTILITIES', 'domain': 'nuprc.gov.ng', 'name': 'Nigerian Upstream Petroleum Regulatory Commission'},
    'NMDPRA': {'category': 'UTILITIES', 'domain': 'nmdpra.gov.ng', 'name': 'Nigerian Midstream and Downstream Petroleum Regulatory Authority'},

    # HEALTH
    'FMOH': {'category': 'HEALTH', 'domain': 'health.gov.ng', 'name': 'Federal Ministry of Health'},
    'NAFDAC': {'category': 'HEALTH', 'domain': 'nafdac.gov.ng', 'name': 'National Agency for Food and Drug Administration and Control'},
    'NHIA': {'category': 'HEALTH', 'domain': 'nhia.gov.ng', 'name': 'National Health Insurance Authority'},

    # EDUCATION
    'FMOE': {'category': 'EDUCATION', 'domain': 'education.gov.ng', 'name': 'Federal Ministry of Education'},
    'NUC': {'category': 'EDUCATION', 'domain': 'nuc.edu.ng', 'name': 'National Universities Commission'},
    'NBTE': {'category': 'EDUCATION', 'domain': 'nbte.gov.ng', 'name': 'National Board for Technical Education'},
    'JAMB': {'category': 'EDUCATION', 'domain': 'jamb.gov.ng', 'name': 'Joint Admissions and Matriculation Board'},

    # STATISTICS
    'NIMC': {'category': 'STATISTICS', 'domain': 'nimc.gov.ng', 'name': 'National Identity Management Commission'},
    'NPC': {'category': 'STATISTICS', 'domain': 'population.gov.ng', 'name': 'National Population Commission'},

    # JUDICIARY
    'NJC': {'category': 'JUDICIARY', 'domain': 'njc.gov.ng', 'name': 'National Judicial Council'},
    'SCN': {'category': 'JUDICIARY', 'domain': 'supremecourt.gov.ng', 'name': 'Supreme Court of Nigeria'},
    'FMJ': {'category': 'JUDICIARY', 'domain': 'justice.gov.ng', 'name': 'Federal Ministry of Justice'},

    # TRANSPORT
    'FMW': {'category': 'TRANSPORT', 'domain': 'works.gov.ng', 'name': 'Federal Ministry of Works'},
    'NPA': {'category': 'TRANSPORT', 'domain': 'nigerianports.gov.ng', 'name': 'Nigerian Ports Authority'},
    'NIMASA': {'category': 'TRANSPORT', 'domain': 'nimasa.gov.ng', 'name': 'Nigerian Maritime Administration and Safety Agency'},
    'NCAA': {'category': 'TRANSPORT', 'domain': 'ncaa.gov.ng', 'name': 'Nigerian Civil Aviation Authority'},
    'NRC': {'category': 'TRANSPORT', 'domain': 'nrc.gov.ng', 'name': 'Nigerian Railway Corporation'},

    # OTHER
    'NCC': {'category': 'OTHER', 'domain': 'ncc.gov.ng', 'name': 'Nigerian Communications Commission'},
    'NITDA': {'category': 'OTHER', 'domain': 'nitda.gov.ng', 'name': 'National Information Technology Development Agency'},
    'FMARD': {'category': 'OTHER', 'domain': 'fmard.gov.ng', 'name': 'Federal Ministry of Agriculture and Rural Development'},

    # ADDITIONAL LEGITIMATE NIGERIAN BODIES
    'FCSC': {'category': 'OTHER', 'domain': 'fedcivilservice.gov.ng', 'name': 'Federal Civil Service Commission'},
    'FMD': {'category': 'SECURITY', 'domain': 'defence.gov.ng', 'name': 'Federal Ministry of Defence'},
    'FMEnv': {'category': 'OTHER', 'domain': 'environment.gov.ng', 'name': 'Federal Ministry of Environment'},
    'FMF': {'category': 'FINANCE', 'domain': 'finance.gov.ng', 'name': 'Federal Ministry of Finance'},
    'FMI': {'category': 'SECURITY', 'domain': 'interior.gov.ng', 'name': 'Federal Ministry of Interior'},
    'FRSC': {'category': 'SECURITY', 'domain': 'frsc.gov.ng', 'name': 'Federal Road Safety Corps'},
    'INEC': {'category': 'OTHER', 'domain': 'inecnigeria.org', 'name': 'Independent National Electoral Commission'},
    'NDLEA': {'category': 'SECURITY', 'domain': 'ndlea.gov.ng', 'name': 'National Drug Law Enforcement Agency'},
    'PSC': {'category': 'SECURITY', 'domain': 'psc.gov.ng', 'name': 'Police Service Commission'},
    'TRCN': {'category': 'EDUCATION', 'domain': 'trcn.gov.ng', 'name': 'Teachers Registration Council of Nigeria'},
    'UBEC': {'category': 'EDUCATION', 'domain': 'ubec.gov.ng', 'name': 'Universal Basic Education Commission'},
}


class Command(BaseCommand):
    help = "Reconcile all Agency records, official_domains, categories, logo_urls, and Portal URLs."

    def handle(self, *args, **options):
        self.stdout.write("Starting Agency & Portal reconciliation...\n")

        # 1. Handle Duplicate Agency: Merge FMA into FMARD
        try:
            fma = Agency.objects.get(acronym='FMA')
            fmard = Agency.objects.get(acronym='FMARD')
            self.stdout.write("Merging duplicate agency 'FMA' into 'FMARD'...")
            
            # Transfer portals
            Portal.objects.filter(agency=fma).update(agency=fmard)
            Alert.objects.filter(agency=fma).update(agency=fmard)
            fma.delete()
            self.stdout.write(self.style.SUCCESS("Merged and deleted FMA."))
        except Agency.DoesNotExist:
            self.stdout.write("No duplicate 'FMA' agency found.")

        # 2. Update Agency Records
        for acronym, info in CANONICAL_AGENCIES.items():
            domain = info['domain']
            category = info['category']
            name = info['name']

            agency, created = Agency.objects.get_or_create(acronym=acronym)
            agency.name = name
            agency.category = category
            agency.official_domains = [domain]
            agency.logo_url = f"https://logo.clearbit.com/{domain}?size=128"
            if not agency.description.strip():
                agency.description = f"Official recruitment portal and telemetry monitoring for {name} ({acronym})."
            agency.save()

            action = "Created" if created else "Updated"
            self.stdout.write(f" [{action}] Agency: {acronym} | Category: {category} | Domain: {domain}")

            # Ensure agency has at least 1 Portal record
            portals = Portal.objects.filter(agency=agency)
            if not portals.exists():
                Portal.objects.create(
                    agency=agency,
                    name=f"{acronym} Recruitment Portal",
                    url=f"https://{domain}/recruitment",
                    health_status='UNKNOWN',
                    status='UNKNOWN',
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f"   + Created missing Portal for {acronym}"))

        # 3. Clean up Portal URLs to prevent duplicate URLs within/across agencies
        for portal in Portal.objects.select_related('agency').all():
            if not portal.agency:
                continue
            domains = portal.agency.official_domains or []
            primary_domain = domains[0] if domains else f"{portal.agency.acronym.lower()}.gov.ng"
            
            # Ensure URL starts with agency domain
            if primary_domain not in portal.url and 'cdcfib.career' in portal.url:
                portal.url = f"https://{primary_domain}/recruitment"
                portal.save(update_fields=['url'])
                self.stdout.write(f"   Fixed Portal URL for {portal.agency.acronym} -> {portal.url}")

        # 4. Resolve intra-agency duplicate URLs (if two portals for same agency have identical URL)
        agencies_with_dupe_portals = Agency.objects.all()
        for agency in agencies_with_dupe_portals:
            p_list = list(Portal.objects.filter(agency=agency).order_by('id'))
            seen_urls = set()
            for p in p_list:
                if p.url in seen_urls:
                    # Differentiate second portal URL (e.g. main website vs recruitment portal)
                    primary_domain = agency.official_domains[0] if agency.official_domains else f"{agency.acronym.lower()}.gov.ng"
                    if "recruitment" in p.url or "careers" in p.url:
                        p.url = f"https://{primary_domain}"
                    else:
                        p.url = f"https://{primary_domain}/careers"
                    p.save(update_fields=['url'])
                    self.stdout.write(f"   Differentiated duplicate Portal URL for {agency.acronym}: {p.name} -> {p.url}")
                else:
                    seen_urls.add(p.url)

        self.stdout.write(self.style.SUCCESS("\nReconciliation complete!"))
