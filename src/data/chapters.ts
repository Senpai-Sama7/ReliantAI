import type { Chapter } from '../sections/PinnedStory';

export const caseStudyChapters: Chapter[] = [
  {
    eyebrow: 'Case Study',
    title: 'METAL FABRICATION',
    description: 'A complete digital transformation for a Houston metal fabrication company. We built a site that showcases their capabilities and generates qualified B2B leads.',
    bullets: [
      'Custom project gallery',
      'Equipment showcase',
      'Quote request system',
      'Industry-specific SEO',
    ],
    stats: [
      { value: '+340%', label: 'Lead increase' },
      { value: '$500K', label: 'New revenue (6mo)' },
      { value: '2.1s', label: 'Load time' },
    ],
    visualSrc: '/project-metalforge.jpg',
    visualAlt: 'Metal fabrication workshop',
    theme: 'light',
  },
  {
    eyebrow: 'Case Study',
    title: 'OILFIELD SERVICES',
    description: 'Premium web presence for an oilfield services company. The site emphasizes safety certifications, fleet capabilities, and 24/7 availability.',
    bullets: [
      'Safety certification display',
      'Fleet visualization',
      'Emergency contact system',
      'Service area mapping',
    ],
    stats: [
      { value: '+180%', label: 'Quote requests' },
      { value: '3 major', label: 'Contracts won' },
      { value: '98%', label: 'Mobile score' },
    ],
    visualSrc: '/project-oilfield.jpg',
    visualAlt: 'Oilfield equipment',
    theme: 'warm',
  },
  {
    eyebrow: 'Case Study',
    title: 'HOME SERVICES',
    description: 'A conversion-focused website for an HVAC company. Features online booking, service area targeting, and seasonal campaign integration.',
    bullets: [
      'Online booking system',
      'Service area pages',
      'Review integration',
      'Seasonal promotions',
    ],
    stats: [
      { value: '60%', label: 'Online bookings' },
      { value: '-40%', label: 'Call volume' },
      { value: '4.9★', label: 'Average rating' },
    ],
    visualSrc: '/project-homeservices.jpg',
    visualAlt: 'Home services professional',
    theme: 'light',
  },
  {
    eyebrow: 'Case Study',
    title: 'MEDICAL PRACTICE',
    description: 'HIPAA-compliant website for a medical group. Patient portal integration, online forms, and automated appointment scheduling.',
    bullets: [
      'HIPAA compliance',
      'Patient portal',
      'Online forms',
      'Insurance verification',
    ],
    stats: [
      { value: '3x', label: 'Appointment rate' },
      { value: '50%', label: 'Form completion' },
      { value: 'A+', label: 'Security audit' },
    ],
    visualSrc: '/project-medical.jpg',
    visualAlt: 'Medical office',
    theme: 'light',
  },
];
