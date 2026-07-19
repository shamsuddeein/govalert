"""
audit_agency_data — Management command to perform a complete system-wide audit of all Agency and Portal records.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.agencies.models import Agency, Portal


ALLOWED_DOMAIN_ENDINGS = ('.gov.ng', '.mil.ng', '.edu.ng', '.org.ng', 'nnpcgroup.com', '.com')


class Command(BaseCommand):
    help = "Audit all agency and portal records for data integrity, duplicate URLs, domain validity, and logo URLs."

    def handle(self, *args, **options):
        self.stdout.write("================================================================================")
        self.stdout.write("                     GOVALERT AGENCY & PORTAL AUDIT REPORT                      ")
        self.stdout.write("================================================================================\n")

        agencies = Agency.objects.prefetch_related('portals').order_by('acronym')
        total_agencies = agencies.count()

        self.stdout.write(f"TOTAL AGENCY COUNT: {total_agencies} (Expected: 41)\n")
        if total_agencies != 41:
            self.stdout.write(self.style.WARNING(f" [FLAG] Total agency count is {total_agencies}, expected 41.\n"))

        agencies_with_zero_portals = []
        suspicious_domains_agencies = []
        suspicious_logo_agencies = []

        self.stdout.write("--------------------------------------------------------------------------------")
        self.stdout.write("PER-AGENCY AUDIT BREAKDOWN")
        self.stdout.write("--------------------------------------------------------------------------------")

        for agency in agencies:
            domains = agency.official_domains or []
            logo = agency.logo_url or ""
            desc = agency.description or ""
            portals = agency.portals.all()
            p_count = portals.count()

            # Audit checks for this agency
            desc_flag = " [EMPTY DESC]" if not desc.strip() else ""
            
            # Check zero portals
            if p_count == 0:
                agencies_with_zero_portals.append(agency.acronym)

            # Check domains
            domain_suspicious = False
            if not domains:
                domain_suspicious = True
            else:
                for d in domains:
                    if not any(d.endswith(ending) for ending in ALLOWED_DOMAIN_ENDINGS):
                        domain_suspicious = True
                        break
            if domain_suspicious:
                suspicious_domains_agencies.append((agency.acronym, domains))

            # Check logo_url
            expected_logo = f"https://logo.clearbit.com/{domains[0]}?size=128" if domains else ""
            logo_suspicious = False
            if not logo or logo != expected_logo:
                logo_suspicious = True
                suspicious_logo_agencies.append((agency.acronym, logo, expected_logo))

            self.stdout.write(
                f"[{agency.acronym}] {agency.name}\n"
                f"   Category: {agency.category} | Vetted Score: {agency.vetted_score}{desc_flag}\n"
                f"   Official Domains: {domains}\n"
                f"   Logo URL: {logo or 'NONE'}\n"
                f"   Portals ({p_count}):"
            )

            if p_count == 0:
                self.stdout.write(self.style.ERROR("      CRITICAL GAP: 0 related portals!"))
            else:
                for p in portals:
                    self.stdout.write(f"      - [{p.health_status}] {p.name} -> {p.url}")
            self.stdout.write("")

        self.stdout.write("--------------------------------------------------------------------------------")
        self.stdout.write("SYSTEMIC ISSUES AUDIT SUMMARY")
        self.stdout.write("--------------------------------------------------------------------------------")

        # 1. Zero Portal Agencies
        if agencies_with_zero_portals:
            self.stdout.write(self.style.ERROR(
                f"[CRITICAL GAP] {len(agencies_with_zero_portals)} Agencies have 0 Portals: " +
                ", ".join(agencies_with_zero_portals)
            ))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] All agencies have at least 1 Portal record."))

        # 2. Duplicate Portal URLs Check
        duplicate_urls = (
            Portal.objects.values('url')
            .annotate(url_count=Count('id'))
            .filter(url_count__gt=1)
        )
        if duplicate_urls.exists():
            self.stdout.write(self.style.ERROR(f"\n[DUPLICATE URLS FOUND] {duplicate_urls.count()} URLs shared across multiple portals:"))
            for item in duplicate_urls:
                url_val = item['url']
                sharing_portals = Portal.objects.filter(url=url_val).select_related('agency')
                self.stdout.write(f"  URL: {url_val} (Used by {item['url_count']} portals):")
                for sp in sharing_portals:
                    self.stdout.write(f"    - Agency: {sp.agency.acronym if sp.agency else 'N/A'} | Portal: {sp.name}")
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] Zero duplicate Portal URLs found across agencies."))

        # 3. Suspicious Official Domains Check
        if suspicious_domains_agencies:
            self.stdout.write(self.style.WARNING(f"\n[SUSPICIOUS DOMAINS] {len(suspicious_domains_agencies)} Agencies with empty or non-standard domains:"))
            for acr, doms in suspicious_domains_agencies:
                self.stdout.write(f"  - [{acr}]: {doms}")
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] All official_domains match expected Nigerian TLDs."))

        # 4. Logo URL Mismatches Check
        if suspicious_logo_agencies:
            self.stdout.write(self.style.WARNING(f"\n[LOGO URL MISMATCHES] {len(suspicious_logo_agencies)} Agencies with incorrect or missing logo_url:"))
            for acr, curr, exp in suspicious_logo_agencies:
                self.stdout.write(f"  - [{acr}]: Current='{curr}' | Expected='{exp}'")
        else:
            self.stdout.write(self.style.SUCCESS("\n[OK] All logo_urls match expected Clearbit pattern."))

        self.stdout.write("\n================================================================================\n")
