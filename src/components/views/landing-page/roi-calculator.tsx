'use client';

import { useState } from 'react';
import { Slider } from '@/components/ui/slider';

interface ROICalculatorProps {
  onApplyClick: () => void;
}

export function ROICalculator({ onApplyClick }: ROICalculatorProps) {
  const [studentCount, setStudentCount] = useState(50);
  const avgRevenuePerStudent = 10000;
  const revenue = studentCount * avgRevenuePerStudent;

  return (
    <div id="roi" className="bg-white text-gray-900 rounded-3xl p-8 md:p-10 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-bosse-green rounded-bl-full opacity-5"></div>
      
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-bosse-blue">Revenue Calculator</h3>
        <div className="p-2 bg-green-50 rounded-lg text-bosse-green"><i className="fa-solid fa-calculator"></i></div>
      </div>
      
      <p className="text-gray-500 text-sm mb-8">Estimate your potential yearly revenue share based on your projected student enrollments.</p>
      
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          <label className="font-semibold text-gray-700">Estimated Students / Year</label>
          <span className="font-bold text-bosse-blue text-xl">{studentCount}</span>
        </div>
        
        <Slider 
          value={[studentCount]}
          onValueChange={(val) => setStudentCount(val[0])}
          max={500}
          min={10}
          step={5}
          className="w-full my-4 cursor-pointer"
        />

        <div className="flex justify-between mt-2 text-xs text-gray-400 font-medium">
          <span>10</span>
          <span>500+</span>
        </div>
      </div>

      <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 text-center mb-6">
        <p className="text-sm text-gray-500 font-medium mb-1">Projected Annual Revenue</p>
        <h4 className="text-4xl font-extrabold text-bosse-green">₹{revenue.toLocaleString('en-IN')}</h4>
        <p className="text-xs text-gray-400 mt-2">*Calculation based on avg. fees. Actuals may vary.</p>
      </div>
      
      <button onClick={onApplyClick} className="w-full bg-bosse-blue text-white py-4 rounded-xl font-bold hover:bg-blue-900 transition-colors shadow-md">
        Claim Your Region Now
      </button>
    </div>
  );
}
