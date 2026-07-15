"""
seed_agencies — Idempotently seeds all 41 monitored Nigerian government agencies.

Usage:
    python manage.py seed_agencies
    python manage.py seed_agencies --dry-run

Uses get_or_create on acronym so it is safe to re-run without duplicating records.
Existing agencies are updated with the latest data from this fixture.
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify


AGENCIES = [
    # ── Security & Law Enforcement ─────────────────────────────────────────
    {
        'name': 'Nigerian Army',
        'acronym': 'Army',
        'category': 'SECURITY',
        'official_domains': ['army.mil.ng'],
        'portal_url': 'https://army.mil.ng/recruitment',
        'description': 'The Nigerian Army is the land warfare branch of the Nigerian Armed Forces.',
        'vetted_score': 95,
        'priority': 'HIGH',
    },
    {
        'name': 'Civil Defence, Correctional, Fire and Immigration Board',
        'acronym': 'CDCFIB',
        'category': 'SECURITY',
        'official_domains': ['cdcfib.gov.ng'],
        'portal_url': 'https://cdcfib.gov.ng/recruitment',
        'description': 'CDCFIB oversees recruitment into civil defence, correctional, fire, and immigration services.',
        'vetted_score': 90,
        'priority': 'HIGH',
    },
    {
        'name': 'Department of State Services',
        'acronym': 'DSS',
        'category': 'SECURITY',
        'official_domains': ['dss.gov.ng'],
        'portal_url': 'https://dss.gov.ng/recruitment',
        'description': 'The DSS is Nigeria\'s primary domestic intelligence agency responsible for national security.',
        'vetted_score': 92,
        'priority': 'HIGH',
    },
    {
        'name': 'Federal Fire Service',
        'acronym': 'FFS',
        'category': 'SECURITY',
        'official_domains': ['fedfire.gov.ng'],
        'portal_url': 'https://fedfire.gov.ng/recruitment',
        'description': 'The Federal Fire Service provides fire prevention and firefighting services across Nigeria.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigerian Air Force',
        'acronym': 'NAF',
        'category': 'SECURITY',
        'official_domains': ['airforce.mil.ng'],
        'portal_url': 'https://nafrecruitment.airforce.mil.ng',
        'description': 'The Nigerian Air Force is the aerial warfare branch of the Nigerian Armed Forces.',
        'vetted_score': 95,
        'priority': 'HIGH',
    },
    {
        'name': 'Nigerian Correctional Service',
        'acronym': 'NCoS',
        'category': 'SECURITY',
        'official_domains': ['corrections.gov.ng'],
        'portal_url': 'https://corrections.gov.ng/recruitment',
        'description': 'The NCoS manages correctional centres and rehabilitation of offenders in Nigeria.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigerian Defence Academy',
        'acronym': 'NDA',
        'category': 'SECURITY',
        'official_domains': ['nda.edu.ng'],
        'portal_url': 'https://nda.edu.ng/recruitment',
        'description': 'The NDA is Nigeria\'s premier military institution for officer cadet training.',
        'vetted_score': 90,
        'priority': 'HIGH',
    },
    {
        'name': 'Nigeria Immigration Service',
        'acronym': 'NIS',
        'category': 'SECURITY',
        'official_domains': ['immigration.gov.ng'],
        'portal_url': 'https://immigration.gov.ng/recruitment',
        'description': 'NIS manages border control, immigration enforcement, and passport issuance in Nigeria.',
        'vetted_score': 90,
        'priority': 'HIGH',
    },
    {
        'name': 'Nigeria Police Force',
        'acronym': 'NPF',
        'category': 'SECURITY',
        'official_domains': ['npf.gov.ng'],
        'portal_url': 'https://npf.gov.ng/recruitment',
        'description': 'The Nigeria Police Force is the primary law enforcement agency of Nigeria.',
        'vetted_score': 90,
        'priority': 'HIGH',
    },
    {
        'name': 'Nigeria Security and Civil Defence Corps',
        'acronym': 'NSCDC',
        'category': 'SECURITY',
        'official_domains': ['nscdc.gov.ng'],
        'portal_url': 'https://nscdc.gov.ng/recruitment',
        'description': 'NSCDC protects critical national infrastructure and supports law enforcement.',
        'vetted_score': 88,
        'priority': 'HIGH',
    },
    {
        'name': 'Nigerian Navy',
        'acronym': 'Navy',
        'category': 'SECURITY',
        'official_domains': ['navy.mil.ng'],
        'portal_url': 'https://navy.mil.ng/recruitment',
        'description': 'The Nigerian Navy is the naval warfare branch of the Nigerian Armed Forces.',
        'vetted_score': 95,
        'priority': 'HIGH',
    },

    # ── Anti-Corruption & Justice ──────────────────────────────────────────
    {
        'name': 'Economic and Financial Crimes Commission',
        'acronym': 'EFCC',
        'category': 'JUDICIARY',
        'official_domains': ['efcc.gov.ng'],
        'portal_url': 'https://efcc.gov.ng/recruitment',
        'description': 'The EFCC investigates and prosecutes financial crimes and economic fraud in Nigeria.',
        'vetted_score': 92,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Independent Corrupt Practices Commission',
        'acronym': 'ICPC',
        'category': 'JUDICIARY',
        'official_domains': ['icpc.gov.ng'],
        'portal_url': 'https://icpc.gov.ng/recruitment',
        'description': 'ICPC fights corruption in public institutions and promotes transparency in government.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },

    # ── Finance & Revenue ─────────────────────────────────────────────────
    {
        'name': 'Central Bank of Nigeria',
        'acronym': 'CBN',
        'category': 'FINANCE',
        'official_domains': ['cbn.gov.ng'],
        'portal_url': 'https://cbn.gov.ng/careers',
        'description': 'CBN is Nigeria\'s apex monetary authority managing monetary policy and financial stability.',
        'vetted_score': 95,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Federal Inland Revenue Service',
        'acronym': 'FIRS',
        'category': 'FINANCE',
        'official_domains': ['firs.gov.ng'],
        'portal_url': 'https://firs.gov.ng/careers',
        'description': 'FIRS is responsible for assessing, collecting, and accounting for tax revenue in Nigeria.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigeria Customs Service',
        'acronym': 'NCS',
        'category': 'FINANCE',
        'official_domains': ['customs.gov.ng'],
        'portal_url': 'https://customs.gov.ng/recruitment',
        'description': 'NCS manages import/export control and revenue collection at Nigeria\'s borders.',
        'vetted_score': 92,
        'priority': 'HIGH',
    },

    # ── Energy & Natural Resources ────────────────────────────────────────
    {
        'name': 'Nigerian National Petroleum Corporation',
        'acronym': 'NNPC',
        'category': 'UTILITIES',
        'official_domains': ['nnpcgroup.com'],
        'portal_url': 'https://nnpcgroup.com/careers',
        'description': 'NNPC is Nigeria\'s state oil company managing the nation\'s petroleum resources.',
        'vetted_score': 92,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigerian Upstream Petroleum Regulatory Commission',
        'acronym': 'NUPRC',
        'category': 'UTILITIES',
        'official_domains': ['nuprc.gov.ng'],
        'portal_url': 'https://nuprc.gov.ng/careers',
        'description': 'NUPRC regulates upstream petroleum operations in Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },
    {
        'name': 'Nigerian Midstream and Downstream Petroleum Regulatory Authority',
        'acronym': 'NMDPRA',
        'category': 'UTILITIES',
        'official_domains': ['nmdpra.gov.ng'],
        'portal_url': 'https://nmdpra.gov.ng/careers',
        'description': 'NMDPRA regulates the midstream and downstream petroleum sector in Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },

    # ── Health ────────────────────────────────────────────────────────────
    {
        'name': 'Federal Ministry of Health',
        'acronym': 'FMOH',
        'category': 'HEALTH',
        'official_domains': ['health.gov.ng'],
        'portal_url': 'https://health.gov.ng/recruitment',
        'description': 'FMOH formulates health policies and manages healthcare delivery across Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },
    {
        'name': 'National Agency for Food and Drug Administration and Control',
        'acronym': 'NAFDAC',
        'category': 'HEALTH',
        'official_domains': ['nafdac.gov.ng'],
        'portal_url': 'https://nafdac.gov.ng/careers',
        'description': 'NAFDAC regulates and controls the manufacture and sale of food, drugs, and cosmetics in Nigeria.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },
    {
        'name': 'National Health Insurance Authority',
        'acronym': 'NHIA',
        'category': 'HEALTH',
        'official_domains': ['nhia.gov.ng'],
        'portal_url': 'https://nhia.gov.ng/recruitment',
        'description': 'NHIA manages Nigeria\'s national health insurance scheme to improve healthcare access.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },

    # ── Education ─────────────────────────────────────────────────────────
    {
        'name': 'Federal Ministry of Education',
        'acronym': 'FMOE',
        'category': 'EDUCATION',
        'official_domains': ['education.gov.ng'],
        'portal_url': 'https://education.gov.ng/recruitment',
        'description': 'FMOE oversees education policy, curriculum, and school systems across Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },
    {
        'name': 'National Universities Commission',
        'acronym': 'NUC',
        'category': 'EDUCATION',
        'official_domains': ['nuc.edu.ng'],
        'portal_url': 'https://nuc.edu.ng/careers',
        'description': 'NUC regulates university education and accredits degree programmes in Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },
    {
        'name': 'National Board for Technical Education',
        'acronym': 'NBTE',
        'category': 'EDUCATION',
        'official_domains': ['nbte.gov.ng'],
        'portal_url': 'https://nbte.gov.ng/careers',
        'description': 'NBTE regulates technical and vocational education institutions in Nigeria.',
        'vetted_score': 82,
        'priority': 'LOW',
    },
    {
        'name': 'Joint Admissions and Matriculation Board',
        'acronym': 'JAMB',
        'category': 'EDUCATION',
        'official_domains': ['jamb.gov.ng'],
        'portal_url': 'https://jamb.gov.ng/recruitment',
        'description': 'JAMB conducts unified entrance examinations for tertiary institutions in Nigeria.',
        'vetted_score': 90,
        'priority': 'MEDIUM',
    },

    # ── Identity & Civil Registration ─────────────────────────────────────
    {
        'name': 'National Identity Management Commission',
        'acronym': 'NIMC',
        'category': 'OTHER',
        'official_domains': ['nimc.gov.ng'],
        'portal_url': 'https://nimc.gov.ng/recruitment',
        'description': 'NIMC manages Nigeria\'s national identity database and issues National Identification Numbers.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },
    {
        'name': 'National Population Commission',
        'acronym': 'NPC',
        'category': 'STATISTICS',
        'official_domains': ['population.gov.ng'],
        'portal_url': 'https://population.gov.ng/recruitment',
        'description': 'NPC conducts population censuses and maintains vital statistics for Nigeria.',
        'vetted_score': 85,
        'priority': 'LOW',
    },

    # ── Justice & Legal ───────────────────────────────────────────────────
    {
        'name': 'National Judicial Council',
        'acronym': 'NJC',
        'category': 'JUDICIARY',
        'official_domains': ['njc.gov.ng'],
        'portal_url': 'https://njc.gov.ng/careers',
        'description': 'NJC manages the appointment, promotion, and discipline of judicial officers in Nigeria.',
        'vetted_score': 88,
        'priority': 'LOW',
    },
    {
        'name': 'Supreme Court of Nigeria',
        'acronym': 'SCN',
        'category': 'JUDICIARY',
        'official_domains': ['supremecourt.gov.ng'],
        'portal_url': 'https://supremecourt.gov.ng/careers',
        'description': 'The Supreme Court of Nigeria is the highest court and final court of appeal.',
        'vetted_score': 90,
        'priority': 'LOW',
    },
    {
        'name': 'Federal Ministry of Justice',
        'acronym': 'FMJ',
        'category': 'JUDICIARY',
        'official_domains': ['justice.gov.ng'],
        'portal_url': 'https://justice.gov.ng/recruitment',
        'description': 'FMJ provides legal advice to the federal government and prosecutes federal crimes.',
        'vetted_score': 85,
        'priority': 'LOW',
    },

    # ── Infrastructure & Transport ────────────────────────────────────────
    {
        'name': 'Federal Ministry of Works',
        'acronym': 'FMW',
        'category': 'TRANSPORT',
        'official_domains': ['works.gov.ng'],
        'portal_url': 'https://works.gov.ng/recruitment',
        'description': 'FMW oversees construction and maintenance of federal highways and infrastructure.',
        'vetted_score': 82,
        'priority': 'LOW',
    },
    {
        'name': 'Nigerian Ports Authority',
        'acronym': 'NPA',
        'category': 'TRANSPORT',
        'official_domains': ['nigerianports.gov.ng'],
        'portal_url': 'https://nigerianports.gov.ng/careers',
        'description': 'NPA manages and develops Nigeria\'s seaport infrastructure and shipping operations.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigerian Maritime Administration and Safety Agency',
        'acronym': 'NIMASA',
        'category': 'TRANSPORT',
        'official_domains': ['nimasa.gov.ng'],
        'portal_url': 'https://nimasa.gov.ng/careers',
        'description': 'NIMASA regulates maritime industry, shipping, and cabotage trade in Nigeria.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },
    {
        'name': 'Nigerian Civil Aviation Authority',
        'acronym': 'NCAA',
        'category': 'TRANSPORT',
        'official_domains': ['ncaa.gov.ng'],
        'portal_url': 'https://ncaa.gov.ng/careers',
        'description': 'NCAA regulates civil aviation safety and licenses aircraft, airlines, and airports.',
        'vetted_score': 88,
        'priority': 'LOW',
    },
    {
        'name': 'Nigerian Railway Corporation',
        'acronym': 'NRC',
        'category': 'TRANSPORT',
        'official_domains': ['nrc.gov.ng'],
        'portal_url': 'https://nrc.gov.ng/recruitment',
        'description': 'NRC manages railway infrastructure and passenger/freight rail services in Nigeria.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },

    # ── Communications & Technology ───────────────────────────────────────
    {
        'name': 'Nigerian Communications Commission',
        'acronym': 'NCC',
        'category': 'OTHER',
        'official_domains': ['ncc.gov.ng'],
        'portal_url': 'https://ncc.gov.ng/careers',
        'description': 'NCC regulates telecommunications services and spectrum management in Nigeria.',
        'vetted_score': 88,
        'priority': 'MEDIUM',
    },
    {
        'name': 'National Information Technology Development Agency',
        'acronym': 'NITDA',
        'category': 'OTHER',
        'official_domains': ['nitda.gov.ng'],
        'portal_url': 'https://nitda.gov.ng/recruitment',
        'description': 'NITDA implements IT policies and drives digital transformation in Nigeria.',
        'vetted_score': 85,
        'priority': 'MEDIUM',
    },

    # ── Agriculture ───────────────────────────────────────────────────────
    {
        'name': 'Federal Ministry of Agriculture and Rural Development',
        'acronym': 'FMARD',
        'category': 'OTHER',
        'official_domains': ['fmard.gov.ng'],
        'portal_url': 'https://fmard.gov.ng/recruitment',
        'description': 'FMARD formulates and implements agricultural policies to enhance food security.',
        'vetted_score': 82,
        'priority': 'LOW',
    },
]


class Command(BaseCommand):
    help = 'Seed all 41 monitored Nigerian government agencies into the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to the database.',
        )

    def handle(self, *args, **options):
        from apps.agencies.models import Agency, Portal, ScrapeMethod
        from django.utils.text import slugify

        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be written.\n'))

        created_count = 0
        updated_count = 0

        for data in AGENCIES:
            acronym = data['acronym']
            name = data['name']
            slug = slugify(acronym)

            if dry_run:
                exists = Agency.objects.filter(name=name).exists()
                action = 'EXISTS' if exists else 'CREATE'
                self.stdout.write(f'  [{action}] {acronym} — {name}')
                continue

            agency, created = Agency.objects.update_or_create(
                name=name,
                defaults={
                    'acronym': acronym,
                    'slug': slug,
                    'category': data['category'],
                    'official_domains': data['official_domains'],
                    'description': data['description'],
                    'vetted_score': data['vetted_score'],
                    'is_active': True,
                }
            )

            if not created:
                updated_count += 1
                self.stdout.write(f'  [UPDATED] {agency.acronym} — {name}')
            else:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  [CREATED] {acronym} — {name}'))

            # Create default portal if none exists for this URL
            portal_url = data['portal_url']
            priority = data.get('priority', 'MEDIUM')
            if not agency.portals.filter(url=portal_url).exists():
                Portal.objects.create(
                    agency=agency,
                    name=f'{agency.acronym} Recruitment Portal',
                    url=portal_url,
                    scrape_method=ScrapeMethod.REQUESTS,
                    priority=priority,
                    is_active=True,
                )
                self.stdout.write(f'    → Portal created: {portal_url}')


        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\nDone. Created: {created_count}, Updated: {updated_count}, '
                f'Total: {Agency.objects.count()} agencies.'
            ))
