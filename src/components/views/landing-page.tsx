'use client';

import { useState, useEffect, useRef } from 'react';
import { type UserProfile } from '@/lib/api';
import { toast } from 'sonner';

import { LoginModal } from './landing-page/login-modal';
import { ApplyModal } from './landing-page/apply-modal';
import { FAQSection } from './landing-page/faq-section';
import { ROICalculator } from './landing-page/roi-calculator';

interface LandingPageProps {
  onLogin: (profile: UserProfile) => void;
}

export function LandingPage({ onLogin }: LandingPageProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Lead Gen State
  const [leadEmail, setLeadEmail] = useState('');
  const [leadLoading, setLeadLoading] = useState(false);

  // Animated Counters State
  const statsRef = useRef<HTMLDivElement>(null);
  const [statsAnimated, setStatsAnimated] = useState(false);
  const [count1, setCount1] = useState(0);
  const [count2, setCount2] = useState(0);
  const [count3, setCount3] = useState(0);
  const [count4, setCount4] = useState(0);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !statsAnimated) {
          setStatsAnimated(true);
        }
      },
      { threshold: 0.1 }
    );
    if (statsRef.current) {
      observer.observe(statsRef.current);
    }
    return () => observer.disconnect();
  }, [statsAnimated]);

  useEffect(() => {
    if (statsAnimated) {
      const animateValue = (setFn: React.Dispatch<React.SetStateAction<number>>, start: number, end: number, duration: number) => {
        let startTimestamp: number | null = null;
        const step = (timestamp: number) => {
          if (!startTimestamp) startTimestamp = timestamp;
          const progress = Math.min((timestamp - startTimestamp) / duration, 1);
          setFn(Math.floor(progress * (end - start) + start));
          if (progress < 1) {
            window.requestAnimationFrame(step);
          }
        };
        window.requestAnimationFrame(step);
      };
      animateValue(setCount1, 0, 10, 2000);
      animateValue(setCount2, 0, 500, 2000);
      animateValue(setCount3, 0, 50000, 2000);
      animateValue(setCount4, 0, 98, 2000);
    }
  }, [statsAnimated]);

  const handleDownload = (e: React.FormEvent) => {
    e.preventDefault();
    setLeadLoading(true);
    setTimeout(() => {
      setLeadLoading(false);
      toast.success('Prospectus Sent. Please check your email inbox.');
      setLeadEmail('');
    }, 1000);
  };

  const openApplyModal = () => {
    setIsApplyModalOpen(true);
    setIsMobileMenuOpen(false);
  };

  return (
    <div className="bg-gray-50 text-gray-800 antialiased overflow-x-hidden pb-20 md:pb-0">
      <nav className={`glass-nav fixed w-full top-0 z-40 transition-all duration-300 ${scrolled ? 'shadow-md' : 'shadow-sm'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-bosse-blue flex items-center justify-center text-white font-bold text-xl shadow-md">
                <i className="fa-solid fa-tree"></i>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-bosse-blue leading-tight">RIMIT</h1>
                <p className="text-xs font-semibold text-bosse-green tracking-widest uppercase">Educations</p>
              </div>
            </div>

            <div className="hidden md:flex items-center space-x-8">
              <a href="#offerings" className="text-gray-600 hover:text-bosse-green font-medium transition-colors">Offerings</a>
              <a href="#process" className="text-gray-600 hover:text-bosse-green font-medium transition-colors">How it Works</a>
              <a href="#benefits" className="text-gray-600 hover:text-bosse-green font-medium transition-colors">Benefits</a>
              <a href="#roi" className="text-gray-600 hover:text-bosse-green font-medium transition-colors">ROI Calc</a>
              <button onClick={() => setIsLoginModalOpen(true)} className="bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 px-5 py-2.5 rounded-full font-medium transition-all shadow-sm flex items-center gap-2">
                <i className="fa-solid fa-user-lock"></i> Login
              </button>
              <button onClick={openApplyModal} className="bg-bosse-blue hover:bg-blue-900 text-white px-6 py-2.5 rounded-full font-medium transition-all duration-300 shadow-md hover:shadow-lg transform hover:-translate-y-0.5">
                Apply Now
              </button>
            </div>

            <div className="md:hidden flex items-center">
              <button onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} className="text-bosse-blue focus:outline-none text-2xl">
                <i className="fa-solid fa-bars"></i>
              </button>
            </div>
          </div>
        </div>
        
        <div className={`${isMobileMenuOpen ? 'block' : 'hidden'} md:hidden bg-white border-t border-gray-100 absolute w-full shadow-lg`}>
          <div className="px-4 pt-2 pb-6 space-y-2 text-center">
            <a href="#offerings" onClick={() => setIsMobileMenuOpen(false)} className="block px-3 py-3 text-gray-700 hover:text-bosse-blue font-medium">Offerings</a>
            <a href="#process" onClick={() => setIsMobileMenuOpen(false)} className="block px-3 py-3 text-gray-700 hover:text-bosse-blue font-medium">How it Works</a>
            <a href="#benefits" onClick={() => setIsMobileMenuOpen(false)} className="block px-3 py-3 text-gray-700 hover:text-bosse-blue font-medium">Benefits</a>
            <button onClick={() => { setIsLoginModalOpen(true); setIsMobileMenuOpen(false); }} className="w-full mt-2 bg-gray-100 text-gray-800 px-6 py-3 rounded-xl font-medium">Partner Login</button>
          </div>
        </div>
      </nav>

      <section className="relative pt-32 pb-16 lg:pt-40 lg:pb-20 overflow-hidden bg-white">
        <div className="absolute top-0 left-0 w-full h-full bg-bosse-light -z-10"></div>
        <div className="absolute top-20 right-0 w-96 h-96 bg-bosse-green rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-fade-in -z-10 text-white"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-slide-up text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 text-bosse-blue font-semibold text-sm mb-6 border border-blue-100">
                <span className="w-2 h-2 rounded-full bg-bosse-green animate-pulse"></span>
                B2B Partner Program 2026 Open
              </div>
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight mb-6">
                Partner with <br/>
                <span className="text-bosse-blue">BOSSE Sikkim!</span>
              </h2>
              <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto lg:mx-0">
                Unlock new business opportunities in the education sector. Grow together, empower education, and build a highly profitable centre with valid certifications.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <button onClick={openApplyModal} className="px-8 py-4 bg-bosse-green hover:bg-green-700 text-white rounded-full font-bold text-lg shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 text-center flex justify-center items-center gap-2">
                  Start Application <i className="fa-solid fa-arrow-right"></i>
                </button>
                <a href="#roi" className="px-8 py-4 bg-white border-2 border-gray-200 text-gray-700 hover:border-bosse-blue hover:text-bosse-blue rounded-full font-bold text-lg shadow-sm transition-all duration-300 text-center flex items-center justify-center">
                  Calculate ROI
                </a>
              </div>
              <p className="mt-4 text-sm text-gray-500 font-medium"><i className="fa-solid fa-check-circle text-bosse-green mr-1"></i> Limited centre approvals available per district.</p>
            </div>

            <div className="relative animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <div className="relative rounded-2xl overflow-hidden shadow-2xl border-4 border-white">
                <img src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80" alt="Team collaborating" className="w-full h-[400px] object-cover transform hover:scale-105 transition-transform duration-700" />
                <div className="absolute inset-0 bg-gradient-to-t from-bosse-blue/80 to-transparent"></div>
                <div className="absolute bottom-6 left-6 right-6 text-white">
                  <p className="text-2xl font-bold mb-1">Stronger Partnership.</p>
                  <p className="text-lg text-blue-100">Greater Impact.</p>
                </div>
              </div>
              
              <div className="absolute -bottom-6 -left-6 bg-white p-4 rounded-xl shadow-xl hidden items-center gap-4 border border-gray-100 md:flex z-10">
                <div className="bg-yellow-100 text-yellow-600 p-3 rounded-full">
                  <i className="fa-solid fa-star text-2xl"></i>
                </div>
                <div>
                  <p className="font-bold text-gray-900">Highly Rewarding</p>
                  <p className="text-sm text-gray-500">B2B Business Model</p>
                </div>
              </div>
              
              <div className="absolute -top-6 -right-6 bg-white p-4 rounded-xl shadow-xl hidden items-center gap-3 border border-gray-100 md:flex z-10">
                <div className="bg-green-100 text-bosse-green p-2 rounded-full">
                  <i className="fa-solid fa-chart-line text-lg"></i>
                </div>
                <p className="font-bold text-gray-900 text-sm">High Growth Rate</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="bg-white border-y border-gray-100 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-6">Recognized & Trusted By</p>
          <div className="flex flex-wrap justify-center gap-8 md:gap-16 items-center opacity-60 grayscale">
            <div className="flex items-center gap-2 text-xl font-bold text-gray-600"><i className="fa-solid fa-building-columns"></i> Gov. Approvals</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-600"><i className="fa-solid fa-certificate"></i> ISO 9001:2015</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-600"><i className="fa-solid fa-globe"></i> Global Accreditations</div>
            <div className="flex items-center gap-2 text-xl font-bold text-gray-600"><i className="fa-solid fa-award"></i> Excellence Awards</div>
          </div>
        </div>
      </div>

      <section ref={statsRef} className="py-16 bg-gray-50 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <h3 className="text-4xl font-extrabold text-bosse-blue mb-2">{count1}+</h3>
              <p className="text-gray-600 font-medium">Years of Excellence</p>
            </div>
            <div>
              <h3 className="text-4xl font-extrabold text-bosse-blue mb-2">{count2}+</h3>
              <p className="text-gray-600 font-medium">Active Study Centres</p>
            </div>
            <div>
              <h3 className="text-4xl font-extrabold text-bosse-blue mb-2">{count3.toLocaleString()}+</h3>
              <p className="text-gray-600 font-medium">Students Enrolled</p>
            </div>
            <div>
              <h3 className="text-4xl font-extrabold text-bosse-green mb-2">{count4}%</h3>
              <p className="text-gray-600 font-medium">Partner Satisfaction</p>
            </div>
          </div>
        </div>
      </section>

      <section id="offerings" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h3 className="text-bosse-green font-bold tracking-wide uppercase mb-2">Our Invitation</h3>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Core Partnership Opportunities</h2>
            <p className="text-lg text-gray-600">The Board of Open Schooling and Skill Education (BOSSE) invites applications. Expand your reach, increase revenue, and create a brighter tomorrow.</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-2xl p-8 border border-gray-100 hover:border-bosse-blue shadow-sm hover:shadow-xl transition-all duration-300 group">
              <div className="w-14 h-14 bg-blue-50 text-bosse-blue rounded-xl flex items-center justify-center text-2xl mb-6 group-hover:scale-110 transition-transform group-hover:bg-bosse-blue group-hover:text-white">
                <i className="fa-solid fa-school"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Authorized Study Centre</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Get official approval to operate as a recognized BOSSE centre in your region and boost your credibility.</p>
            </div>

            <div className="bg-white rounded-2xl p-8 border border-gray-100 hover:border-bosse-green shadow-sm hover:shadow-xl transition-all duration-300 group">
              <div className="w-14 h-14 bg-green-50 text-bosse-green rounded-xl flex items-center justify-center text-2xl mb-6 group-hover:scale-110 transition-transform group-hover:bg-bosse-green group-hover:text-white">
                <i className="fa-solid fa-users"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Direct Admissions</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Seamlessly process admissions for Secondary (10th) & Senior Secondary (12th) programs for your students.</p>
            </div>

            <div className="bg-white rounded-2xl p-8 border border-gray-100 hover:border-bosse-blue shadow-sm hover:shadow-xl transition-all duration-300 group">
              <div className="w-14 h-14 bg-blue-50 text-bosse-blue rounded-xl flex items-center justify-center text-2xl mb-6 group-hover:scale-110 transition-transform group-hover:bg-bosse-blue group-hover:text-white">
                <i className="fa-solid fa-handshake"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Exclusive Partnership</h3>
              <p className="text-gray-600 text-sm leading-relaxed">A highly rewarding B2B model designed for educational consultants and coaching institutes.</p>
            </div>

            <div className="bg-white rounded-2xl p-8 border border-gray-100 hover:border-bosse-green shadow-sm hover:shadow-xl transition-all duration-300 group">
              <div className="w-14 h-14 bg-green-50 text-bosse-green rounded-xl flex items-center justify-center text-2xl mb-6 group-hover:scale-110 transition-transform group-hover:bg-bosse-green group-hover:text-white">
                <i className="fa-solid fa-chart-line"></i>
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">High Revenue Potential</h3>
              <p className="text-gray-600 text-sm leading-relaxed">Maximize your growth and expand your educational services with excellent revenue sharing.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="process" className="py-20 bg-gray-50 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Simple Onboarding Process</h2>
            <p className="text-lg text-gray-600">Become a recognized partner in 4 straightforward steps.</p>
          </div>

          <div className="relative">
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-1 bg-blue-100 -translate-y-1/2 z-0"></div>
            
            <div className="grid md:grid-cols-4 gap-8 relative z-10">
              <div className="text-center relative">
                <div className="w-16 h-16 mx-auto bg-white border-4 border-bosse-blue text-bosse-blue rounded-full flex items-center justify-center text-xl font-bold shadow-md mb-4 relative z-10">1</div>
                <h4 className="font-bold text-lg mb-2">Apply Online</h4>
                <p className="text-sm text-gray-500">Fill out our quick partnership application form to initiate the process.</p>
              </div>
              <div className="text-center relative">
                <div className="w-16 h-16 mx-auto bg-white border-4 border-blue-300 text-blue-400 rounded-full flex items-center justify-center text-xl font-bold shadow-md mb-4 relative z-10">2</div>
                <h4 className="font-bold text-lg mb-2">Document Review</h4>
                <p className="text-sm text-gray-500">Our team reviews your institution's credentials and infrastructure details.</p>
              </div>
              <div className="text-center relative">
                <div className="w-16 h-16 mx-auto bg-white border-4 border-blue-300 text-blue-400 rounded-full flex items-center justify-center text-xl font-bold shadow-md mb-4 relative z-10">3</div>
                <h4 className="font-bold text-lg mb-2">MOU & Agreement</h4>
                <p className="text-sm text-gray-500">Sign the official Memorandum of Understanding outlining our mutual growth.</p>
              </div>
              <div className="text-center relative">
                <div className="w-16 h-16 mx-auto bg-bosse-green border-4 border-green-200 text-white rounded-full flex items-center justify-center text-xl font-bold shadow-md mb-4 relative z-10"><i className="fa-solid fa-rocket"></i></div>
                <h4 className="font-bold text-lg mb-2">Launch Centre</h4>
                <p className="text-sm text-gray-500">Receive your official certificate, marketing kit, and start admissions!</p>
              </div>
            </div>
          </div>
          
          <div className="text-center mt-12">
            <button onClick={openApplyModal} className="px-8 py-3 bg-bosse-blue hover:bg-blue-900 text-white rounded-full font-bold shadow-md transition-colors">Start Step 1 Now</button>
          </div>
        </div>
      </section>

      <section id="benefits" className="py-20 gradient-bg text-white relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            
            <div>
              <h3 className="text-bosse-gold font-bold tracking-wide uppercase mb-2">The Advantage</h3>
              <h2 className="text-3xl md:text-4xl font-bold mb-8">Why Partner With Us?</h2>
              
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="bg-white/10 p-3 rounded-lg mt-1 shrink-0">
                    <i className="fa-solid fa-globe text-bosse-gold text-xl"></i>
                  </div>
                  <div>
                    <h4 className="text-xl font-bold mb-1">Global Recognition</h4>
                    <p className="text-blue-100 text-sm leading-relaxed">Our certifications are globally recognized, making them valid for higher education and government/private employment opportunities.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="bg-white/10 p-3 rounded-lg mt-1 shrink-0">
                    <i className="fa-solid fa-headset text-bosse-gold text-xl"></i>
                  </div>
                  <div>
                    <h4 className="text-xl font-bold mb-1">Complete Ecosystem Support</h4>
                    <p className="text-blue-100 text-sm leading-relaxed">End-to-end operational support including marketing collateral, staff training, CRM portal access, and dedicated account managers.</p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="bg-white/10 p-3 rounded-lg mt-1 shrink-0">
                    <i className="fa-solid fa-clipboard-check text-bosse-gold text-xl"></i>
                  </div>
                  <div>
                    <h4 className="text-xl font-bold mb-1">Frictionless Operations</h4>
                    <p className="text-blue-100 text-sm leading-relaxed">Streamlined, transparent digital admission and examination processes to save you time and reduce administrative overhead.</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-10 pt-8 border-t border-white/20">
                <h4 className="font-bold text-lg mb-4">Who Should Apply?</h4>
                <div className="flex flex-wrap gap-2">
                  <span className="px-4 py-2 bg-white/10 rounded-full text-sm font-medium border border-white/20">Schools</span>
                  <span className="px-4 py-2 bg-white/10 rounded-full text-sm font-medium border border-white/20">Tuition Centers</span>
                  <span className="px-4 py-2 bg-white/10 rounded-full text-sm font-medium border border-white/20">Consultants</span>
                  <span className="px-4 py-2 bg-white/10 rounded-full text-sm font-medium border border-white/20">Entrepreneurs</span>
                </div>
              </div>
            </div>

            <ROICalculator onApplyClick={openApplyModal} />

          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Partner Success Stories</h2>
            <p className="text-gray-600">Hear from institutions that have transformed their business with BOSSE.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gray-50 p-8 rounded-2xl border border-gray-100 relative">
              <i className="fa-solid fa-quote-right absolute top-6 right-6 text-4xl text-gray-200"></i>
              <div className="flex text-yellow-400 text-sm mb-4">
                <i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i>
              </div>
              <p className="text-gray-700 italic mb-6">"Partnering with BOSSE allowed us to offer recognized 10th and 12th certifications. Our enrollment doubled in just 6 months, and the portal makes admissions a breeze."</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-200 flex items-center justify-center font-bold text-bosse-blue">RK</div>
                <div>
                  <p className="font-bold text-gray-900 text-sm">Rahul K.</p>
                  <p className="text-xs text-gray-500">Director, Excel Academy</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-8 rounded-2xl border border-gray-100 relative">
              <i className="fa-solid fa-quote-right absolute top-6 right-6 text-4xl text-gray-200"></i>
              <div className="flex text-yellow-400 text-sm mb-4">
                <i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i>
              </div>
              <p className="text-gray-700 italic mb-6">"The B2B revenue sharing model is highly transparent. The support team at BOSSE Sikkim is always responsive, helping us resolve student queries instantly."</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-200 flex items-center justify-center font-bold text-bosse-green">SM</div>
                <div>
                  <p className="font-bold text-gray-900 text-sm">Sneha M.</p>
                  <p className="text-xs text-gray-500">Educational Consultant</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-8 rounded-2xl border border-gray-100 relative">
              <i className="fa-solid fa-quote-right absolute top-6 right-6 text-4xl text-gray-200"></i>
              <div className="flex text-yellow-400 text-sm mb-4">
                <i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i><i className="fa-solid fa-star"></i>
              </div>
              <p className="text-gray-700 italic mb-6">"We upgraded our coaching center to an Authorized Study Centre. The prestige of being associated with a recognized board has elevated our brand locally."</p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-200 flex items-center justify-center font-bold text-bosse-blue">VP</div>
                <div>
                  <p className="font-bold text-gray-900 text-sm">Vikram P.</p>
                  <p className="text-xs text-gray-500">Founder, Vidya Institute</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <FAQSection />

      <section className="bg-bosse-green py-12 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white rounded-full mix-blend-overlay opacity-10 -translate-y-1/2 translate-x-1/2"></div>
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">Want to review detailed margins & requirements?</h2>
          <p className="text-green-100 mb-8 max-w-2xl mx-auto">Download our comprehensive 2026 Partnership Prospectus PDF directly to your inbox.</p>
          
          <form onSubmit={handleDownload} className="flex flex-col sm:flex-row gap-3 justify-center max-w-xl mx-auto">
            <input 
              type="email" 
              required 
              value={leadEmail}
              onChange={(e) => setLeadEmail(e.target.value)}
              placeholder="Enter your business email" 
              className="flex-1 px-4 py-3 rounded-lg border-0 focus:ring-2 focus:ring-white bg-white/10 text-white placeholder-green-200 outline-none" 
            />
            <button disabled={leadLoading} type="submit" className="px-6 py-3 bg-white text-bosse-green font-bold rounded-lg hover:bg-gray-100 transition-colors shadow-lg flex items-center justify-center gap-2">
              {leadLoading ? <><i className="fa-solid fa-spinner fa-spin"></i> Sending...</> : <><i className="fa-solid fa-download"></i> Get Prospectus</>}
            </button>
          </form>
        </div>
      </section>

      <footer className="bg-gray-900 text-white pt-20 pb-24 md:pb-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-12 border-b border-gray-800 pb-16">
            <div className="lg:col-span-1">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-bosse-green flex items-center justify-center text-white font-bold shadow-md">
                  <i className="fa-solid fa-tree"></i>
                </div>
                <h2 className="text-2xl font-bold text-white tracking-wide">BOSSE Sikkim</h2>
              </div>
              <p className="text-gray-400 mb-6 leading-relaxed text-sm">
                Empowering education through valid certifications and highly rewarding B2B partnerships. Let's build a brighter tomorrow together.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-6 text-white border-l-4 border-bosse-green pl-3">Quick Links</h3>
              <ul className="space-y-3 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-bosse-green transition-colors"><i className="fa-solid fa-angle-right mr-2"></i> Home</a></li>
                <li><a href="#offerings" className="hover:text-bosse-green transition-colors"><i className="fa-solid fa-angle-right mr-2"></i> Partnership Programs</a></li>
                <li><a href="#process" className="hover:text-bosse-green transition-colors"><i className="fa-solid fa-angle-right mr-2"></i> How to Apply</a></li>
                <li><button onClick={() => setIsLoginModalOpen(true)} className="hover:text-bosse-green transition-colors"><i className="fa-solid fa-angle-right mr-2"></i> Partner Portal Login</button></li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-bold mb-6 text-white border-l-4 border-bosse-gold pl-3">Contact Admissions Cell</h3>
              <div className="space-y-4 text-gray-300 text-sm">
                <div className="flex items-start gap-3">
                  <div className="text-bosse-green mt-1"><i className="fa-solid fa-phone-volume"></i></div>
                  <div>
                    <p className="font-medium">+91 9778469227</p>
                    <p className="font-medium">+91 9288088809</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-bosse-green"><i className="fa-solid fa-envelope"></i></div>
                  <a href="mailto:haseenabosse@gmail.com" className="hover:text-white transition-colors">haseenabosse@gmail.com</a>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-bosse-green"><i className="fa-solid fa-globe"></i></div>
                  <a href="http://www.bosse.ac.in" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">www.bosse.ac.in</a>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-8 text-center text-gray-500 text-xs flex flex-col md:flex-row justify-between items-center gap-4">
            <p>&copy; 2026 Board of Open Schooling and Skill Education, Sikkim. B2B Landing Page.</p>
          </div>
        </div>
      </footer>
      
      <div className="md:hidden fixed bottom-0 left-0 w-full bg-white shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.1)] z-30 p-3 border-t border-gray-200 animate-slide-up">
        <button onClick={openApplyModal} className="w-full bg-bosse-green text-white py-3.5 rounded-xl font-bold shadow-md flex items-center justify-center gap-2">
          Apply For Partnership <i className="fa-solid fa-bolt text-yellow-300"></i>
        </button>
      </div>

      <LoginModal 
        isOpen={isLoginModalOpen} 
        onOpenChange={setIsLoginModalOpen} 
        onLogin={onLogin} 
      />

      <ApplyModal 
        isOpen={isApplyModalOpen} 
        onOpenChange={setIsApplyModalOpen} 
      />
    </div>
  );
}
