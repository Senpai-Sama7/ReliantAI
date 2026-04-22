import { useState, useEffect } from 'react';
import api, { type Customer, type PricingPlan, type RevenueSummary } from '../../services/api';
import { 
  DollarSign, 
  Users, 
  CreditCard, 
  Mail, 
  Phone, 
  Building2,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Copy,
  Send
} from 'lucide-react';

interface PricingCardProps {
  plan: PricingPlan;
  planId: string;
  isPopular?: boolean;
  onSelect: (planId: string) => void;
}

function PricingCard({ plan, planId, isPopular, onSelect }: PricingCardProps) {
  return (
    <div 
      className={`relative p-6 border ${isPopular ? 'border-genh-gold' : 'border-genh-gray/30'} bg-genh-charcoal/50`}
      style={{ clipPath: 'polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 0 100%)' }}
    >
      {isPopular && (
        <div className="absolute -top-3 left-6">
          <span className="bg-genh-gold text-genh-black text-xs font-bold px-3 py-1 uppercase tracking-wider">
            Most Popular
          </span>
        </div>
      )}
      
      <div className="mb-6">
        <h3 className="font-display text-xl text-genh-white mb-2">{plan.name}</h3>
        <div className="flex items-baseline gap-1">
          <span className="font-display text-4xl text-genh-gold">${plan.price}</span>
          <span className="text-genh-gray">/month</span>
        </div>
      </div>
      
      <div className="mb-6">
        <p className="text-sm text-genh-gray mb-2">
          {plan.dispatches_per_month === -1 ? 'Unlimited dispatches' : `${plan.dispatches_per_month} dispatches/month`}
        </p>
      </div>
      
      <ul className="space-y-3 mb-6">
        {plan.features.map((feature, idx) => (
          <li key={idx} className="flex items-start gap-2 text-sm text-genh-white/80">
            <CheckCircle className="w-4 h-4 text-genh-gold mt-0.5 shrink-0" />
            {feature}
          </li>
        ))}
      </ul>
      
      <button
        onClick={() => onSelect(planId)}
        className={`w-full py-3 px-4 font-body uppercase tracking-wider text-sm transition-colors ${
          isPopular 
            ? 'bg-genh-gold text-genh-black hover:bg-genh-gold/90' 
            : 'border border-genh-gold text-genh-gold hover:bg-genh-gold/10'
        }`}
      >
        {plan.price === 0 ? 'Get Started Free' : 'Subscribe Now'}
      </button>
    </div>
  );
}

interface CustomerRowProps {
  customer: Customer;
  onUpdate: (customer: Customer) => void;
}

function CustomerRow({ customer, onUpdate }: CustomerRowProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [outreachNote, setOutreachNote] = useState(customer.notes || '');
  
  const statusColors: Record<string, string> = {
    active: 'text-green-400 bg-green-400/10',
    inactive: 'text-genh-gray bg-genh-gray/10',
    past_due: 'text-red-400 bg-red-400/10',
    cancelled: 'text-genh-gray bg-genh-gray/10',
  };
  
  const outreachColors: Record<string, string> = {
    new: 'text-blue-400 bg-blue-400/10',
    contacted: 'text-yellow-400 bg-yellow-400/10',
    qualified: 'text-green-400 bg-green-400/10',
    proposal: 'text-purple-400 bg-purple-400/10',
    closed_won: 'text-green-400 bg-green-400/20',
    closed_lost: 'text-genh-gray bg-genh-gray/20',
  };

  const copyApiKey = () => {
    navigator.clipboard.writeText(customer.api_key_masked);
  };

  return (
    <div className="border-b border-genh-gray/20">
      <div 
        className="grid grid-cols-12 gap-4 p-4 items-center cursor-pointer hover:bg-genh-charcoal/30 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="col-span-3">
          <p className="font-medium text-genh-white">{customer.name || customer.email}</p>
          <p className="text-sm text-genh-gray">{customer.company}</p>
        </div>
        
        <div className="col-span-2">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-body uppercase tracking-wider border ${statusColors[customer.billing_status] || statusColors.inactive}`}>
            {customer.billing_status}
          </span>
        </div>
        
        <div className="col-span-2">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-body uppercase tracking-wider border ${outreachColors[customer.outreach_status] || outreachColors.new}`}>
            {customer.outreach_status}
          </span>
        </div>
        
        <div className="col-span-2">
          <p className="text-genh-gold font-medium">${customer.monthly_revenue || 0}/mo</p>
          <p className="text-xs text-genh-gray">{customer.plan}</p>
        </div>
        
        <div className="col-span-2">
          <p className="text-sm text-genh-white/80">{customer.api_key_masked}</p>
          <button 
            onClick={(e) => { e.stopPropagation(); copyApiKey(); }}
            className="text-xs text-genh-gold hover:underline flex items-center gap-1 mt-1"
          >
            <Copy className="w-3 h-3" /> Copy API Key
          </button>
        </div>
        
        <div className="col-span-1 flex justify-end">
          {isExpanded ? <ChevronUp className="w-5 h-5 text-genh-gray" /> : <ChevronDown className="w-5 h-5 text-genh-gray" />}
        </div>
      </div>
      
      {isExpanded && (
        <div className="p-4 bg-genh-charcoal/20 border-t border-genh-gray/10">
          <div className="grid grid-cols-2 gap-6 mb-4">
            <div>
              <h4 className="text-label mb-3 text-genh-gray">Contact Information</h4>
              <div className="space-y-2 text-sm">
                <p className="flex items-center gap-2 text-genh-white/80">
                  <Mail className="w-4 h-4 text-genh-gold" />
                  {customer.email}
                </p>
                {customer.phone && (
                  <p className="flex items-center gap-2 text-genh-white/80">
                    <Phone className="w-4 h-4 text-genh-gold" />
                    {customer.phone}
                  </p>
                )}
                <p className="flex items-center gap-2 text-genh-white/80">
                  <Building2 className="w-4 h-4 text-genh-gold" />
                  {customer.company || 'No company'}
                </p>
              </div>
            </div>
            
            <div>
              <h4 className="text-label mb-3 text-genh-gray">Subscription Details</h4>
              <div className="space-y-2 text-sm">
                <p className="text-genh-white/80">Plan: <span className="text-genh-gold">{customer.plan}</span></p>
                <p className="text-genh-white/80">Status: <span className={statusColors[customer.billing_status]}>{customer.billing_status}</span></p>
                {customer.trial_ends_at && (
                  <p className="text-genh-white/80">
                    Trial ends: {new Date(customer.trial_ends_at).toLocaleDateString()}
                  </p>
                )}
                <p className="text-genh-white/80">Created: {new Date(customer.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
          
          <div className="mb-4">
            <h4 className="text-label mb-3 text-genh-gray">Outreach Notes</h4>
            <textarea
              value={outreachNote}
              onChange={(e) => setOutreachNote(e.target.value)}
              className="w-full bg-genh-black/50 border border-genh-gray/30 p-3 text-genh-white text-sm focus:border-genh-gold focus:outline-none"
              rows={3}
              placeholder="Add notes about customer interactions..."
            />
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => onUpdate({ ...customer, notes: outreachNote, outreach_status: 'contacted' })}
              className="flex items-center gap-2 px-4 py-2 bg-genh-gold/20 text-genh-gold text-sm font-body uppercase tracking-wider hover:bg-genh-gold/30 transition-colors"
            >
              <Send className="w-4 h-4" />
              Mark Contacted
            </button>
            <button
              onClick={() => onUpdate({ ...customer, notes: outreachNote, outreach_status: 'qualified' })}
              className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 text-sm font-body uppercase tracking-wider hover:bg-green-500/30 transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              Mark Qualified
            </button>
            <button
              onClick={() => onUpdate({ ...customer, notes: outreachNote, outreach_status: 'closed_won' })}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 text-sm font-body uppercase tracking-wider hover:bg-blue-500/30 transition-colors"
            >
              <DollarSign className="w-4 h-4" />
              Mark Closed Won
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface OutreachTemplate {
  name: string;
  subject: string;
  body: string;
}

const outreachTemplates: OutreachTemplate[] = [
  {
    name: 'Cold Intro',
    subject: 'Quick question about HVAC emergency response',
    body: `Hi {{name}},

I help HVAC companies capture emergency calls that normally go to voicemail after hours.

Our AI responds in seconds, 24/7, triages the urgency, and dispatches your technician automatically.

One Houston customer increased after-hours leads by 35% in the first month.

Worth a 5-minute chat?

Best regards`,
  },
  {
    name: 'Follow-up',
    subject: 'Following up on HVAC AI dispatch',
    body: `Hi {{name}},

Just following up on my email about the AI dispatch system.

I wanted to share a quick case study: One of our customers, {{company}}, saved 15 hours/week on manual dispatching and captured 35% more emergency calls.

Happy to show you a quick demo whenever you're free.

Best regards`,
  },
  {
    name: 'Trial Ending',
    subject: 'Your trial ends soon - quick setup help?',
    body: `Hi {{name}},

I noticed your trial ends in a few days. Want to make sure you're getting the most out of the system.

I can help you:
- Set up your technician phone numbers
- Configure your escalation rules
- Test a few dispatches to make sure everything flows

Takes about 10 minutes. Interested?

Best regards`,
  },
];

export default function BillingPanel() {
  const [activeTab, setActiveTab] = useState<'pricing' | 'customers' | 'revenue' | 'outreach'>('pricing');
  const [pricing, setPricing] = useState<Record<string, PricingPlan> | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<OutreachTemplate>(outreachTemplates[0]);
  const [templateVars, setTemplateVars] = useState<{ name: string; company: string }>({ 
    name: '{{name}}', 
    company: '{{company}}' 
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [pricingData, customersData, revenueData] = await Promise.all([
        api.getPricing(),
        api.listCustomers(),
        api.getRevenue(30),
      ]);
      setPricing(pricingData.plans);
      setCustomers(customersData.customers);
      setRevenue(revenueData);
    } catch (error) {
      console.error('Failed to load billing data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlanSelect = (planId: string) => {
    // In a real app, this would redirect to checkout or show a modal
    alert(`Selected plan: ${planId}. This would redirect to Stripe checkout.`);
  };

  const handleCustomerUpdate = async (customer: Customer) => {
    try {
      // In a real app, this would call the API
      // await api.updateCustomerOutreach(customer.id, customer);
      
      // For now, just update locally
      setCustomers(prev => prev.map(c => c.id === customer.id ? customer : c));
    } catch (error) {
      console.error('Failed to update customer:', error);
    }
  };

  const fillTemplate = (template: string) => {
    return template
      .replace(/\{\{name\}\}/g, templateVars.name)
      .replace(/\{\{company\}\}/g, templateVars.company);
  };

  const copyTemplate = () => {
    navigator.clipboard.writeText(fillTemplate(selectedTemplate.body));
  };

  if (isLoading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-genh-gold border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Tab Navigation */}
      <div className="flex gap-1 border-b border-genh-gray/30">
        {[
          { id: 'pricing', label: 'Pricing', icon: CreditCard },
          { id: 'customers', label: 'Customers', icon: Users },
          { id: 'revenue', label: 'Revenue', icon: DollarSign },
          { id: 'outreach', label: 'Outreach', icon: Send },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-6 py-4 font-body uppercase tracking-wider text-sm transition-colors border-b-2 ${
              activeTab === tab.id 
                ? 'border-genh-gold text-genh-gold' 
                : 'border-transparent text-genh-gray hover:text-genh-white'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Pricing Tab */}
      {activeTab === 'pricing' && pricing && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {Object.entries(pricing).map(([planId, plan]) => (
              <PricingCard
                key={planId}
                plan={plan}
                planId={planId}
                isPopular={planId === 'professional'}
                onSelect={handlePlanSelect}
              />
            ))}
          </div>
          
          <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/30">
            <h3 className="font-display text-lg text-genh-white mb-4">Plan Comparison</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-genh-gray/30">
                    <th className="text-left py-3 px-4 text-genh-gray font-body uppercase tracking-wider">Feature</th>
                    {Object.entries(pricing).map(([planId, plan]) => (
                      <th key={planId} className="text-center py-3 px-4 text-genh-white font-body uppercase tracking-wider">
                        {plan.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-genh-gray/20">
                    <td className="py-3 px-4 text-genh-white/80">Dispatches per month</td>
                    {Object.entries(pricing).map(([planId, plan]) => (
                      <td key={planId} className="text-center py-3 px-4 text-genh-white">
                        {plan.dispatches_per_month === -1 ? 'Unlimited' : plan.dispatches_per_month}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b border-genh-gray/20">
                    <td className="py-3 px-4 text-genh-white/80">API Access</td>
                    {Object.entries(pricing).map(([planId, plan]) => (
                      <td key={planId} className="text-center py-3 px-4">
                        {plan.features.includes('API access') ? (
                          <CheckCircle className="w-5 h-5 text-green-400 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-genh-gray mx-auto" />
                        )}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-b border-genh-gray/20">
                    <td className="py-3 px-4 text-genh-white/80">Priority Support</td>
                    {Object.entries(pricing).map(([planId, plan]) => (
                      <td key={planId} className="text-center py-3 px-4">
                        {plan.features.some(f => f.includes('Priority') || f.includes('24/7')) ? (
                          <CheckCircle className="w-5 h-5 text-green-400 mx-auto" />
                        ) : (
                          <XCircle className="w-5 h-5 text-genh-gray mx-auto" />
                        )}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Customers Tab */}
      {activeTab === 'customers' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-lg text-genh-white">
              Customers ({customers.length})
            </h3>
            <div className="flex gap-2">
              <button 
                onClick={loadData}
                className="px-4 py-2 border border-genh-gray/30 text-genh-white text-sm hover:bg-genh-charcoal/50 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
          
          <div className="border border-genh-gray/30 bg-genh-charcoal/20">
            <div className="grid grid-cols-12 gap-4 p-4 border-b border-genh-gray/30 bg-genh-charcoal/30">
              <div className="col-span-3 text-label text-genh-gray uppercase tracking-wider">Customer</div>
              <div className="col-span-2 text-label text-genh-gray uppercase tracking-wider">Billing</div>
              <div className="col-span-2 text-label text-genh-gray uppercase tracking-wider">Outreach</div>
              <div className="col-span-2 text-label text-genh-gray uppercase tracking-wider">Revenue</div>
              <div className="col-span-2 text-label text-genh-gray uppercase tracking-wider">API Key</div>
              <div className="col-span-1"></div>
            </div>
            
            {customers.length === 0 ? (
              <div className="p-8 text-center text-genh-gray">
                <Users className="w-12 h-12 mx-auto mb-4 opacity-30" />
                <p>No customers yet. Create your first customer to get started.</p>
              </div>
            ) : (
              customers.map((customer) => (
                <CustomerRow 
                  key={customer.id} 
                  customer={customer} 
                  onUpdate={handleCustomerUpdate}
                />
              ))
            )}
          </div>
        </div>
      )}

      {/* Revenue Tab */}
      {activeTab === 'revenue' && revenue && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="p-6 border border-genh-gold/30 bg-genh-charcoal/50">
              <p className="text-label mb-2 text-genh-gray">Total Revenue (30d)</p>
              <p className="font-display text-3xl text-genh-gold">${revenue.total_revenue.toFixed(2)}</p>
            </div>
            <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/50">
              <p className="text-label mb-2 text-genh-gray">Active Customers</p>
              <p className="font-display text-3xl text-genh-white">{revenue.active_customers}</p>
            </div>
            <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/50">
              <p className="text-label mb-2 text-genh-gray">MRR Estimate</p>
              <p className="font-display text-3xl text-genh-white">${revenue.mrr_estimate.toFixed(2)}</p>
            </div>
            <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/50">
              <p className="text-label mb-2 text-genh-gray">Total Events</p>
              <p className="font-display text-3xl text-genh-white">{revenue.total_events}</p>
            </div>
          </div>
          
          <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/20">
            <h3 className="font-display text-lg text-genh-white mb-4">Revenue Breakdown</h3>
            <p className="text-genh-gray">
              Detailed revenue analytics will be available here once more customers are onboarded.
            </p>
          </div>
        </div>
      )}

      {/* Outreach Tab */}
      {activeTab === 'outreach' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Template Selection */}
            <div className="space-y-4">
              <h3 className="font-display text-lg text-genh-white">Outreach Templates</h3>
              
              <div className="space-y-2">
                {outreachTemplates.map((template) => (
                  <button
                    key={template.name}
                    onClick={() => setSelectedTemplate(template)}
                    className={`w-full text-left p-4 border transition-colors ${
                      selectedTemplate.name === template.name
                        ? 'border-genh-gold bg-genh-gold/10'
                        : 'border-genh-gray/30 hover:border-genh-gray/50'
                    }`}
                  >
                    <p className="font-medium text-genh-white">{template.name}</p>
                    <p className="text-sm text-genh-gray truncate">{template.subject}</p>
                  </button>
                ))}
              </div>
              
              <div className="p-4 border border-genh-gray/30 bg-genh-charcoal/20">
                <h4 className="text-label mb-3 text-genh-gray">Template Variables</h4>
                <div className="space-y-3">
                  <div>
                    <label className="text-sm text-genh-gray">Customer Name</label>
                    <input
                      type="text"
                      value={templateVars.name}
                      onChange={(e) => setTemplateVars(prev => ({ ...prev, name: e.target.value }))}
                      className="w-full bg-genh-black/50 border border-genh-gray/30 p-2 text-genh-white text-sm focus:border-genh-gold focus:outline-none mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-sm text-genh-gray">Company Name</label>
                    <input
                      type="text"
                      value={templateVars.company}
                      onChange={(e) => setTemplateVars(prev => ({ ...prev, company: e.target.value }))}
                      className="w-full bg-genh-black/50 border border-genh-gray/30 p-2 text-genh-white text-sm focus:border-genh-gold focus:outline-none mt-1"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            {/* Template Preview */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-lg text-genh-white">Preview</h3>
                <button
                  onClick={copyTemplate}
                  className="flex items-center gap-2 px-3 py-1 text-sm text-genh-gold hover:bg-genh-gold/10 transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  Copy
                </button>
              </div>
              
              <div className="p-6 border border-genh-gray/30 bg-genh-charcoal/20">
                <div className="mb-4">
                  <p className="text-label text-genh-gray mb-1">Subject</p>
                  <p className="text-genh-white">{selectedTemplate.subject}</p>
                </div>
                <div>
                  <p className="text-label text-genh-gray mb-1">Body</p>
                  <pre className="text-genh-white/80 whitespace-pre-wrap font-body text-sm">
                    {fillTemplate(selectedTemplate.body)}
                  </pre>
                </div>
              </div>
              
              <div className="p-4 border border-genh-gold/30 bg-genh-gold/10">
                <h4 className="text-label mb-2 text-genh-gold">Quick Actions</h4>
                <div className="space-y-2 text-sm text-genh-white/80">
                  <p>• Use these templates in your CRM or email tool</p>
                  <p>• Personalize with {'{{'+'name'+'}}'} and {'{{'+'company'+'}}'} variables</p>
                  <p>• Track responses in the Customers tab</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
