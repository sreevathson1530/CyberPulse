export interface Person {
  id: string
  name: string
  role: string
  dept: string
  admin: boolean
  devices: string[]
  countries: string[]
  filesPerTenMinutes: number
}

export interface OrgProfile {
  id: string
  name: string
  form: string
  city: string
  headcount: number
  people: Person[]
  officeIps: string[]
  sharedDevices: string[]
  allowedForwardDomains: string[]
  personalMailDomains: string[]
  approvedApps: string[]
  adminRoles: string[]
}

export const PEOPLE: Person[] = [
  {
    id: 'divya',
    name: 'Divya Suresh',
    role: 'Accounts Lead',
    dept: 'Finance',
    admin: false,
    devices: ['LAPTOP-FIN-04', 'IPHONE-DIVYA'],
    countries: ['IN'],
    filesPerTenMinutes: 3,
  },
  {
    id: 'priya',
    name: 'Priya Raghavan',
    role: 'Managing Director',
    dept: 'Leadership',
    admin: true,
    devices: ['MACBOOK-MD-01', 'IPHONE-MD-01'],
    countries: ['IN', 'SG'],
    filesPerTenMinutes: 5,
  },
  {
    id: 'arjun',
    name: 'Arjun Menon',
    role: 'Sales Manager',
    dept: 'Sales',
    admin: false,
    devices: ['LAPTOP-SALES-11', 'IPHONE-SALES-11'],
    countries: ['IN'],
    filesPerTenMinutes: 4,
  },
  {
    id: 'karthik',
    name: 'Karthik Balaji',
    role: 'Dispatch Coordinator',
    dept: 'Operations',
    admin: false,
    devices: ['LAPTOP-OPS-07'],
    countries: ['IN'],
    filesPerTenMinutes: 5,
  },
  {
    id: 'meera',
    name: 'Meera Iyer',
    role: 'HR Manager',
    dept: 'People',
    admin: false,
    devices: ['LAPTOP-HR-02', 'IPHONE-HR-02'],
    countries: ['IN'],
    filesPerTenMinutes: 3,
  },
  {
    id: 'rahim',
    name: 'Rahim Sheikh',
    role: 'Purchase Officer',
    dept: 'Procurement',
    admin: false,
    devices: ['DESKTOP-PUR-01'],
    countries: ['IN', 'AE'],
    filesPerTenMinutes: 4,
  },
  {
    id: 'nithya',
    name: 'Nithya Krishnan',
    role: 'Design Lead',
    dept: 'Studio',
    admin: false,
    devices: ['LAPTOP-STU-03'],
    countries: ['IN'],
    filesPerTenMinutes: 9,
  },
  {
    id: 'vikram',
    name: 'Vikram Anand',
    role: 'IT Support',
    dept: 'Operations',
    admin: true,
    devices: ['LAPTOP-IT-01'],
    countries: ['IN', 'DE'],
    filesPerTenMinutes: 12,
  },
  {
    id: 'sowmya',
    name: 'Sowmya Rajan',
    role: 'Accounts Executive',
    dept: 'Finance',
    admin: false,
    devices: ['DESKTOP-ACC-02'],
    countries: ['IN'],
    filesPerTenMinutes: 6,
  },
  {
    id: 'ganesh',
    name: 'Ganesh Kumar',
    role: 'Warehouse Supervisor',
    dept: 'Operations',
    admin: false,
    devices: ['TAB-WH-05'],
    countries: ['IN'],
    filesPerTenMinutes: 2,
  },
  {
    id: 'anitha',
    name: 'Anitha Rao',
    role: 'Support Executive',
    dept: 'Sales',
    admin: false,
    devices: ['LAPTOP-SUP-08'],
    countries: ['IN'],
    filesPerTenMinutes: 3,
  },
  {
    id: 'joseph',
    name: 'Joseph Daniel',
    role: 'Production Planner',
    dept: 'Operations',
    admin: false,
    devices: ['DESKTOP-PRD-01'],
    countries: ['IN'],
    filesPerTenMinutes: 4,
  },
]

export const ORG: OrgProfile = {
  id: 'vanavil',
  name: 'Vanavil Textiles',
  form: 'Private Limited',
  city: 'Tiruppur, Tamil Nadu',
  headcount: 28,
  people: PEOPLE,
  officeIps: ['203.0.113.24', '203.0.113.25'],
  sharedDevices: ['RECEPTION-PC-01', 'KIOSK-WH-02'],
  allowedForwardDomains: ['vanavil.example'],
  personalMailDomains: ['gmail.example', 'outlook.example', 'proton.example', 'yahoo.example'],
  approvedApps: ['Xero', 'Tally Sync', 'Google Drive'],
  adminRoles: ['Global Admin', 'Billing Admin'],
}

const peopleById = new Map(PEOPLE.map((p) => [p.id, p]))

export function person(id: string): Person {
  return (
    peopleById.get(id) ?? {
      id,
      name: id,
      role: 'Contractor',
      dept: 'External',
      admin: false,
      devices: [],
      countries: ['IN'],
      filesPerTenMinutes: 2,
    }
  )
}

export function personName(id: string): string {
  return person(id).name
}

export function listNames(ids: string[]): string {
  const names = ids.map(personName)
  if (names.length <= 1) return names[0] ?? ''
  if (names.length === 2) return `${names[0]} and ${names[1]}`
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
}
