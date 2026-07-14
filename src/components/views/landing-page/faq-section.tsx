'use client';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export function FAQSection() {
  return (
    <section className="py-20 bg-gray-50 border-t border-gray-100">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
          <p className="text-gray-600">Got questions? We've got answers.</p>
        </div>

        <Accordion type="single" collapsible className="w-full space-y-4">
          <AccordionItem value="item-1" className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm data-[state=open]:shadow-md transition-shadow">
            <AccordionTrigger className="text-left font-semibold text-gray-900 hover:no-underline py-4">
              What is the initial investment required?
            </AccordionTrigger>
            <AccordionContent className="text-gray-600 text-sm leading-relaxed pb-4">
              The initial setup fee is highly competitive and depends on the tier of partnership you choose (Basic Centre vs. Regional Franchise). We discuss full financials transparently during the introductory call.
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-2" className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm data-[state=open]:shadow-md transition-shadow">
            <AccordionTrigger className="text-left font-semibold text-gray-900 hover:no-underline py-4">
              How long does the approval process take?
            </AccordionTrigger>
            <AccordionContent className="text-gray-600 text-sm leading-relaxed pb-4">
              Once your online application is submitted along with necessary documents, our verification team typically processes and grants approval within 7 to 10 business days.
            </AccordionContent>
          </AccordionItem>

          <AccordionItem value="item-3" className="bg-white border border-gray-200 rounded-xl px-6 shadow-sm data-[state=open]:shadow-md transition-shadow">
            <AccordionTrigger className="text-left font-semibold text-gray-900 hover:no-underline py-4">
              Are the certificates valid for Govt. jobs?
            </AccordionTrigger>
            <AccordionContent className="text-gray-600 text-sm leading-relaxed pb-4">
              Yes. The Board of Open Schooling and Skill Education (BOSSE) is a legally established board. Its certifications are valid for higher education admissions and government/private employment across India.
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </section>
  );
}
