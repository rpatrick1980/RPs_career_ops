import { promises as fs } from 'fs';

const urls = [
  { url: 'https://ictjobs.ch/support-it-services/application-supporter-digital-trust-platform/', company: 'Hugentobler', role: 'Application Supporter Digital Trust Platform 100%' },
  { url: 'https://ictjobs.ch/support-it-services/applikationsmanager-sap-80-100/', company: 'Suva', role: 'Applikationsmanager SAP 80–100%' },
  { url: 'https://ictjobs.ch/support-it-services/teamleiterin-it-operations-80-100/', company: 'Paszti', role: 'Teamleiter:in IT Operations 80–100%' },
  { url: 'https://www.jobs.ch/en/vacancies/detail/dbf08fc2-674c-4f2b-af59-7e2df40cc8da/', company: 'SVA Zurich', role: 'Service Manager IT Infrastructure (80%-100%)' },
  { url: 'https://www.jobs.ch/en/vacancies/detail/85bea83f-772c-44cd-b189-964561150ee8/', company: 'MS Reinsurance', role: 'IT Service Manager' },
];

// Quick accessibility test
console.log('Testing URL accessibility...');
for (const item of urls) {
  try {
    const response = await fetch(item.url, { method: 'HEAD', timeout: 5000 });
    console.log(`${item.url.substring(0, 60)}... : ${response.status}`);
  } catch (e) {
    console.log(`${item.url.substring(0, 60)}... : ERROR - ${e.message}`);
  }
}
