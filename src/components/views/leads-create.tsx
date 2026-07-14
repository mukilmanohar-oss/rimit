import { useState } from 'react';
import { UserProfile, admissions } from '@/lib/api';

export function LeadsCreateView({ profile }: { profile: UserProfile }) {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    full_name: '', dob: '', gender: '', religion: '', marital_status: '', aadhar_number: '',
    primary_phone: '', email: '', parent_name: '', parent_phone: '', category: '',
    address_line_1: '', address_line_2: '', city: '', state: '', pincode: '', country: 'India', address_type: 'Permanent',
    employment_status: '', qualification: '', institution: '', year_of_passing: '', 
    examination: '', score_type: 'percentage', score_value: '', percentage_marks: ''
  });

  const update = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const nextStep = () => setStep(s => Math.min(s + 1, 3));
  const prevStep = () => setStep(s => Math.max(s - 1, 1));

    const handleSubmit = async () => {
    setSubmitting(true);
    try {
      let address_block = undefined;
      if (formData.address_line_1 && formData.city && formData.state && formData.pincode) {
        address_block = {
          perm_domicile_type: 'Other',
          perm_address: formData.address_line_1 + (formData.address_line_2 ? ', ' + formData.address_line_2 : ''),
          perm_country: formData.country || 'India',
          perm_state: formData.state,
          perm_district: formData.city,
          perm_city: formData.city,
          perm_pincode: formData.pincode,
          corr_address: formData.address_line_1 + (formData.address_line_2 ? ', ' + formData.address_line_2 : ''),
          corr_country: formData.country || 'India',
          corr_state: formData.state,
          corr_district: formData.city,
          corr_city: formData.city,
          corr_pincode: formData.pincode,
        };
      }

      const payload = {
        full_name: formData.full_name,
        dob: formData.dob || undefined,
        gender: formData.gender || undefined,
        religion: formData.religion || undefined,
        marital_status: formData.marital_status || undefined,
        category: formData.category || undefined,
        aadhar_number: formData.aadhar_number || undefined,
        primary_phone: formData.primary_phone,
        email: formData.email,
        parent_name: formData.parent_name || undefined,
        parent_phone: formData.parent_phone || undefined,
        address_block: address_block,
        academic_histories: formData.qualification ? [{
          qualification: formData.qualification,
          institution: formData.institution || 'N/A',
          board_university: formData.institution || 'N/A',
          year_of_passing: formData.year_of_passing ? parseInt(formData.year_of_passing) : undefined,
          examination: formData.examination,
          score_type: formData.score_type,
          score_value: formData.score_value ? parseFloat(formData.score_value) : undefined,
          percentage_marks: formData.percentage_marks ? parseFloat(formData.percentage_marks) : undefined,
          result: 'Pass'
        }] : [],
        employment_status: formData.employment_status || undefined,
      };

      await admissions.createStudent(payload);
      setSuccess(true);
    } catch (e: any) {
      alert("Error creating lead: " + (e.response?.data ? JSON.stringify(e.response.data) : e.message));
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] bg-card rounded-xl border border-border shadow-sm p-10 text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mb-6">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
        </div>
        <h2 className="text-2xl font-bold mb-2 text-foreground">Lead Created Successfully!</h2>
        <p className="text-muted-foreground mb-8">The student profile has been added to the system.</p>
        <button 
          onClick={() => { setSuccess(false); setStep(1); setFormData({} as any); }}
          className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Create Another Lead
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Lead Generator Wizard</h1>
        <p className="text-muted-foreground mt-1">Universal intake flow for new prospects and leads.</p>
      </div>

      <div className="bg-card rounded-xl border border-border shadow-sm overflow-hidden flex flex-col sm:flex-row min-h-[600px]">
        {/* Sidebar steps */}
        <div className="bg-muted/30 w-full sm:w-64 p-6 border-b sm:border-b-0 sm:border-r border-border flex flex-col gap-6 shrink-0">
          {[
            { num: 1, title: 'Contact & Demographics', desc: 'Basic info & identity' },
            { num: 2, title: 'Residential Details', desc: 'Address information' },
            { num: 3, title: 'Academics & Employment', desc: 'Background & eligibility' }
          ].map((s) => (
            <div key={s.num} className="flex gap-4 items-start">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm shrink-0 transition-colors ${step === s.num ? 'bg-primary text-primary-foreground' : step > s.num ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                {step > s.num ? '✓' : s.num}
              </div>
              <div>
                <h3 className={`font-semibold text-sm ${step === s.num ? 'text-foreground' : 'text-muted-foreground'}`}>{s.title}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Form Content */}
        <div className="flex-1 p-6 sm:p-10 flex flex-col relative overflow-y-auto">
          <div className="flex-1">
            {step === 1 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <h2 className="text-xl font-semibold mb-6">Contact & Demographics</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <Input label="Full Name *" value={formData.full_name} onChange={v => update('full_name', v)} placeholder="John Doe" />
                  <Input label="Primary Phone *" value={formData.primary_phone} onChange={v => update('primary_phone', v)} placeholder="9876543210" />
                  <Input label="Email Address *" type="email" value={formData.email} onChange={v => update('email', v)} placeholder="john@example.com" />
                  <Input label="Date of Birth" type="date" value={formData.dob} onChange={v => update('dob', v)} />
                  <Select label="Gender" value={formData.gender} onChange={v => update('gender', v)} options={[{value: 'M', label: 'Male'}, {value: 'F', label: 'Female'}, {value: 'O', label: 'Other'}]} />
                  <Input label="Aadhar Number" value={formData.aadhar_number} onChange={v => update('aadhar_number', v)} placeholder="12 digit number" />
                  <Select label="Religion" value={formData.religion} onChange={v => update('religion', v)} options={['Hindu', 'Muslim', 'Christian', 'Sikh', 'Other']} />
                  <Select label="Category" value={formData.category} onChange={v => update('category', v)} options={['General', 'OBC', 'SC', 'ST']} />
                  <Select label="Marital Status" value={formData.marital_status} onChange={v => update('marital_status', v)} options={['Single', 'Married', 'Divorced', 'Widowed']} />
                  <Input label="Parent's Name" value={formData.parent_name} onChange={v => update('parent_name', v)} />
                  <Input label="Parent's Phone" value={formData.parent_phone} onChange={v => update('parent_phone', v)} />
                </div>
              </div>
            )}
            
            {step === 2 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <h2 className="text-xl font-semibold mb-6">Residential Details</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="md:col-span-2">
                    <Input label="Address Line 1 *" value={formData.address_line_1} onChange={v => update('address_line_1', v)} placeholder="House/Flat No, Street Name" />
                  </div>
                  <div className="md:col-span-2">
                    <Input label="Address Line 2" value={formData.address_line_2} onChange={v => update('address_line_2', v)} placeholder="Locality, Landmark" />
                  </div>
                  <Input label="City *" value={formData.city} onChange={v => update('city', v)} />
                  <Input label="State *" value={formData.state} onChange={v => update('state', v)} />
                  <Input label="Pincode *" value={formData.pincode} onChange={v => update('pincode', v)} />
                  <Input label="Country" value={formData.country} onChange={v => update('country', v)} />
                  <Select label="Address Type" value={formData.address_type} onChange={v => update('address_type', v)} options={['Permanent', 'Current', 'Office']} />
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="animate-in fade-in slide-in-from-right-4 duration-300">
                <h2 className="text-xl font-semibold mb-6">Academics & Employment</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <Select label="Employment Status" value={formData.employment_status} onChange={v => update('employment_status', v)} options={['Student', 'Employed', 'Unemployed', 'Self-Employed']} />
                  <div className="col-span-1 md:col-span-2 h-px bg-border my-2"></div>
                  <Select label="Highest Qualification" value={formData.qualification} onChange={v => update('qualification', v)} options={['10th', '12th', 'Diploma', 'UG Degree', 'PG Degree']} />
                  <Input label="Institution/University" value={formData.institution} onChange={v => update('institution', v)} />
                  <Input label="Examination/Degree Name" value={formData.examination} onChange={v => update('examination', v)} placeholder="e.g. B.Tech CS" />
                  <Input label="Year of Passing" type="number" value={formData.year_of_passing} onChange={v => update('year_of_passing', v)} />
                  <Select label="Score Type" value={formData.score_type} onChange={v => update('score_type', v)} options={[{value: 'percentage', label: 'Percentage'}, {value: 'cgpa', label: 'CGPA'}]} />
                  <Input label="Score Value" type="number" step="0.01" value={formData.score_value} onChange={v => update('score_value', v)} />
                  <Input label="Equivalent Percentage (%)" type="number" step="0.01" value={formData.percentage_marks} onChange={v => update('percentage_marks', v)} />
                </div>
              </div>
            )}
          </div>

          <div className="mt-10 pt-6 border-t border-border flex justify-between items-center bg-card">
            <button
              onClick={prevStep}
              disabled={step === 1 || submitting}
              className={`px-5 py-2 rounded-lg font-medium transition-colors ${step === 1 ? 'opacity-0 pointer-events-none' : 'text-foreground hover:bg-muted bg-transparent border border-input'}`}
            >
              Back
            </button>
            {step < 3 ? (
              <button
                onClick={nextStep}
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-lg font-medium transition-colors ml-auto flex items-center gap-2"
              >
                Continue
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2 rounded-lg font-medium transition-colors ml-auto flex items-center gap-2 disabled:opacity-70"
              >
                {submitting ? 'Creating...' : 'Create Lead'}
                {!submitting && <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Input({ label, type = 'text', value, onChange, placeholder, step }: any) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-foreground">{label}</label>
      <input 
        type={type} 
        value={value} 
        onChange={e => onChange(e.target.value)} 
        placeholder={placeholder}
        step={step}
        className="px-3 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-shadow placeholder:text-muted-foreground/60" 
      />
    </div>
  );
}

function Select({ label, value, onChange, options }: any) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-foreground">{label}</label>
      <select 
        value={value} 
        onChange={e => onChange(e.target.value)}
        className="px-3 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary transition-shadow"
      >
        <option value="">Select...</option>
        {options.map((o: any) => {
          const val = typeof o === 'string' ? o : o.value;
          const lbl = typeof o === 'string' ? o : o.label;
          return <option key={val} value={val}>{lbl}</option>;
        })}
      </select>
    </div>
  );
}
