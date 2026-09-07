export interface HistoricalRecruitment {
  year: string;
  title: string;
  cadres: string[];
  status: "completed" | "cancelled" | "archived";
}

export interface Agency {
  short: string;
  name: string;
  category: string;
  portalStatus: "online" | "review" | "closed" | "warning";
  lastChecked: string;
  description: string;
  activeCount: number;
  historyCount: number;
  officialWebsite: string;
  recruitmentPortal: string;
  history: HistoricalRecruitment[];
  trustScore: number;
}

export const agenciesData: Agency[] = [
  {
    short: "NNPC",
    name: "NNPC Limited",
    category: "Energy and Resources",
    portalStatus: "online",
    lastChecked: "2 mins ago",
    description:
      "The NNPC Limited (formerly Nigerian National Petroleum Corporation) is the commercialized state oil corporation of Nigeria. It manages the nation's petroleum exploration, refining, and distribution operations, making it one of the most sought-after employers in the country.",
    activeCount: 1,
    historyCount: 7,
    officialWebsite: "https://nnpcgroup.com",
    recruitmentPortal: "https://careers.nnpcgroup.com",
    trustScore: 100,
    history: [
      {
        year: "2024",
        title: "Graduate Trainee Program",
        cadres: ["Engineering Trainees", "Geosciences Trainees", "Finance & Account Trainees"],
        status: "completed",
      },
      {
        year: "2022",
        title: "Experienced Professional Hires",
        cadres: ["Senior Drilling Engineers", "Subsurface Specialists", "Legal Counsel"],
        status: "completed",
      },
      {
        year: "2019",
        title: "General Recruitment Campaign",
        cadres: ["Graduate Trainees", "Experienced Professionals", "Supervisors"],
        status: "archived",
      },
    ],
  },
  {
    short: "NCS",
    name: "Nigeria Customs Service",
    category: "Civil Service",
    portalStatus: "online",
    lastChecked: "5 mins ago",
    description:
      "The Nigeria Customs Service (NCS) is a paramilitary organization under the Federal Ministry of Finance. It is responsible for the collection of customs revenue, prevention of smuggling activities, and trade facilitation across all land borders and maritime ports.",
    activeCount: 1,
    historyCount: 9,
    officialWebsite: "https://customs.gov.ng",
    recruitmentPortal: "https://recruitment.customs.gov.ng",
    trustScore: 96,
    history: [
      {
        year: "2024",
        title: "Superintendent and Inspector Cadres",
        cadres: ["Assistant Superintendent II", "Inspector of Customs", "Customs Assistant"],
        status: "completed",
      },
      {
        year: "2022",
        title: "General Duty Recruitment",
        cadres: ["Customs Officers", "Baggage Officers", "Marine Command recruits"],
        status: "completed",
      },
    ],
  },
  {
    short: "EFCC",
    name: "Economic and Financial Crimes Commission",
    category: "Security and Law Enforcement",
    portalStatus: "online",
    lastChecked: "12 mins ago",
    description:
      "The Economic and Financial Crimes Commission (EFCC) is a law enforcement agency that investigates financial crimes. It is tasked with the prevention, detection, and prosecution of financial fraud, money laundering, and embezzlement across public and private sectors.",
    activeCount: 1,
    historyCount: 6,
    officialWebsite: "https://efcc.gov.ng",
    recruitmentPortal: "https://www.efcc.gov.ng/careers",
    trustScore: 97,
    history: [
      {
        year: "2024",
        title: "Detective Assistant Enlistment",
        cadres: ["Detective Assistants", "Detective Inspectors"],
        status: "completed",
      },
      {
        year: "2023",
        title: "Special Detective Cadet Course",
        cadres: ["Cybercrime Investigators", "Forensic Accountants"],
        status: "completed",
      },
    ],
  },
  {
    short: "CBN",
    name: "Central Bank of Nigeria",
    category: "Finance and Revenue",
    portalStatus: "warning",
    lastChecked: "4 mins ago",
    description:
      "The Central Bank of Nigeria (CBN) is the apex monetary authority of the Federal Republic of Nigeria. It regulates the financial sector, manages the Naira, controls inflation, and drives national monetary policy guidelines.",
    activeCount: 1,
    historyCount: 3,
    officialWebsite: "https://cbn.gov.ng",
    recruitmentPortal: "https://www.cbn.gov.ng/recruitment",
    trustScore: 88,
    history: [
      {
        year: "2024",
        title: "Quantitative Analysts & Economist intake",
        cadres: ["Economic Policy Analysts", "Risk Modellers"],
        status: "completed",
      },
      {
        year: "2021",
        title: "Specialist Professional intake",
        cadres: ["Information Security Specialists", "Banking Supervisors"],
        status: "completed",
      },
    ],
  },
  {
    short: "NAF",
    name: "Nigerian Air Force",
    category: "Civil Service",
    portalStatus: "closed",
    lastChecked: "1h ago",
    description:
      "The Nigerian Air Force (NAF) is the air branch of the Nigerian Armed Forces. It stands as one of the largest in Africa, charged with securing Nigeria's airspace, conducting aerial reconnaissance, and supporting land and maritime forces.",
    activeCount: 0,
    historyCount: 11,
    officialWebsite: "https://airforce.mil.ng",
    recruitmentPortal: "https://nafrecruitment.airforce.mil.ng",
    trustScore: 95,
    history: [
      {
        year: "2024",
        title: "Direct Short Service Commission (DSSC Course 33)",
        cadres: ["Medical Officers", "Engineers", "Legal Officers", "IT Specialists"],
        status: "completed",
      },
      {
        year: "2023",
        title: "Airmen / Airwomen Enlistment (BMTC 44)",
        cadres: ["General Duty Tradesmen", "Non-Tradesmen"],
        status: "completed",
      },
    ],
  },
  {
    short: "FFS",
    name: "Federal Fire Service",
    category: "Security and Law Enforcement",
    portalStatus: "online",
    lastChecked: "14 mins ago",
    description:
      "The Federal Fire Service is the principal fire prevention and rescue body in Nigeria. Under the Ministry of Interior, it enforces national fire safety codes, inspects federal infrastructure, and responds to public fire outbreaks and disasters.",
    activeCount: 1,
    historyCount: 5,
    officialWebsite: "https://fedfire.gov.ng",
    recruitmentPortal: "https://fedfire.gov.ng/recruitment",
    trustScore: 94,
    history: [
      {
        year: "2024",
        title: "General Duty Firefighters Batch B",
        cadres: ["Assistant Superintendent", "Inspector of Fire", "Fire Assistant"],
        status: "completed",
      },
      {
        year: "2021",
        title: "Command Recruitment Exercise",
        cadres: ["General Duty Officers", "Drivers & Mechanics"],
        status: "completed",
      },
    ],
  },
  {
    short: "NIMC",
    name: "National Identity Management Commission",
    category: "Energy and Resources",
    portalStatus: "online",
    lastChecked: "8 mins ago",
    description:
      "The National Identity Management Commission (NIMC) is the federal body responsible for national identification systems, biometric databases, National Identification Number (NIN) registrations, and identity verification.",
    activeCount: 1,
    historyCount: 4,
    officialWebsite: "https://nimc.gov.ng",
    recruitmentPortal: "https://careers.nimc.gov.ng",
    trustScore: 100,
    history: [
      {
        year: "2024",
        title: "Core Infrastructure Team Recruitment",
        cadres: ["Lead Cloud Engineer", "Database Administrator", "DevOps Engineers"],
        status: "completed",
      },
    ],
  },
  {
    short: "FIRS",
    name: "Federal Inland Revenue Service",
    category: "Finance and Revenue",
    portalStatus: "review",
    lastChecked: "24 mins ago",
    description:
      "The Federal Inland Revenue Service is the primary tax collecting authority of the Federal Government of Nigeria. It assesses, collects, and accounts for corporate tax, value-added tax (VAT), and other federal revenue streams.",
    activeCount: 1,
    historyCount: 8,
    officialWebsite: "https://firs.gov.ng",
    recruitmentPortal: "https://firs.gov.ng/careers",
    trustScore: 95,
    history: [
      {
        year: "2024",
        title: "Tax Auditor II Intake",
        cadres: ["Tax Auditors", "Tax Policy Officers", "Legal Analysts"],
        status: "completed",
      },
    ],
  },
  {
    short: "NPF",
    name: "Nigeria Police Force",
    category: "Security and Law Enforcement",
    portalStatus: "online",
    lastChecked: "15 mins ago",
    description:
      "The Nigeria Police Force is the lead internal security agency in Nigeria, operating across all 36 states and the Federal Capital Territory under the Police Service Commission.",
    activeCount: 1,
    historyCount: 14,
    officialWebsite: "https://npf.gov.ng",
    recruitmentPortal: "https://npfrecruitment.gov.ng",
    trustScore: 93,
    history: [
      {
        year: "2024",
        title: "Cadet Inspector Intake",
        cadres: ["Cadet Inspectors", "Police Constables"],
        status: "completed",
      },
    ],
  },
  {
    short: "NPA",
    name: "Nigerian Ports Authority",
    category: "Transport and Infrastructure",
    portalStatus: "review",
    lastChecked: "30 mins ago",
    description:
      "The Nigerian Ports Authority (NPA) oversees and operates all major ports in Nigeria, including Lagos Port Complex (Apapa), Tin Can Island Port, Port Harcourt Port, and Calabar Port.",
    activeCount: 1,
    historyCount: 5,
    officialWebsite: "https://nigerianports.gov.ng",
    recruitmentPortal: "https://careers.nigerianports.gov.ng",
    trustScore: 94,
    history: [
      {
        year: "2024",
        title: "Marine Cadets Scheme",
        cadres: ["Marine Engineering Trainees", "Harbour Masters"],
        status: "completed",
      },
    ],
  },
  {
    short: "FMOH",
    name: "Federal Ministry of Health",
    category: "Health",
    portalStatus: "online",
    lastChecked: "45 mins ago",
    description:
      "The Federal Ministry of Health formulations govern primary, secondary, and tertiary public healthcare assets. It oversees national medical commissions and coordinates health worker recruitment programs.",
    activeCount: 1,
    historyCount: 8,
    officialWebsite: "https://health.gov.ng",
    recruitmentPortal: "https://recruitment.health.gov.ng",
    trustScore: 95,
    history: [
      {
        year: "2024",
        title: "Medical Specialist & Resident Program",
        cadres: ["Medical Officers", "Pharmacists", "Nursing Officers"],
        status: "completed",
      },
    ],
  },
  {
    short: "FMOE",
    name: "Federal Ministry of Education",
    category: "Education",
    portalStatus: "closed",
    lastChecked: "2h ago",
    description:
      "The Federal Ministry of Education administers and coordinates national educational standards, secondary schools (unity schools), and funding programs for federal tertiary institutions.",
    activeCount: 0,
    historyCount: 10,
    officialWebsite: "https://education.gov.ng",
    recruitmentPortal: "https://education.gov.ng/recruitments",
    trustScore: 93,
    history: [
      {
        year: "2023",
        title: "Federal Teachers Scheme",
        cadres: ["Education Instructors", "Administrative Staff"],
        status: "completed",
      },
    ],
  },
  {
    short: "SCN",
    name: "Supreme Court of Nigeria",
    category: "Judiciary",
    portalStatus: "online",
    lastChecked: "3h ago",
    description:
      "The Supreme Court of Nigeria is the highest judicial court, exercising ultimate appellate jurisdiction over all other courts in the federation.",
    activeCount: 1,
    historyCount: 2,
    officialWebsite: "https://supremecourt.gov.ng",
    recruitmentPortal: "https://supremecourt.gov.ng/careers",
    trustScore: 97,
    history: [
      {
        year: "2024",
        title: "Legal Research Cadre",
        cadres: ["Senior Legal Research Officers", "Judicial Assistants"],
        status: "completed",
      },
    ],
  },
  {
    short: "INEC",
    name: "Independent National Electoral Commission",
    category: "Civil Service",
    portalStatus: "online",
    lastChecked: "Just now",
    description:
      "The Independent National Electoral Commission (INEC) is the electoral management body responsible for organizing elections in Nigeria.",
    activeCount: 1,
    historyCount: 5,
    officialWebsite: "https://inecnigeria.org",
    recruitmentPortal: "https://recruitment.inecnigeria.org",
    trustScore: 98,
    history: [
      {
        year: "2024",
        title: "Ad-hoc Staff & Election Registration",
        cadres: ["Registration Officers", "Collation Officers", "Supervisory Officers"],
        status: "completed",
      },
    ],
  },
];
