import React, { useState } from 'react';

interface CalculatorProps {
  onCalculate?: (result: number) => void;
}

export const InteractiveCalculator: React.FC<CalculatorProps> = ({ onCalculate }) => {
  const [homeSize, setHomeSize] = useState(2000);
  const [climate, setClimate] = useState('moderate');
  const [currentSystem, setCurrentSystem] = useState('old');

  const calculateCost = () => {
    const baseCost = homeSize * 0.08;
    const climateMultiplier = climate === 'hot' ? 1.3 : climate === 'cold' ? 1.2 : 1;
    const systemMultiplier = currentSystem === 'none' ? 1.5 : 1;

    return Math.round(baseCost * climateMultiplier * systemMultiplier);
  };

  const estimatedCost = calculateCost();
  const estimatedSavings = Math.round((estimatedCost * 0.15) / 12);

  return (
    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-8 max-w-lg mx-auto">
      <h2 className="text-2xl font-bold text-slate-900 mb-6">Energy Savings Calculator</h2>

      <div className="space-y-6">
        {/* Home Size Slider */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">
            Home Size: {homeSize} sq ft
          </label>
          <input
            type="range"
            min="500"
            max="5000"
            step="100"
            value={homeSize}
            onChange={(e) => setHomeSize(parseInt(e.target.value))}
            className="w-full h-2 bg-blue-300 rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Climate Zone */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Climate Zone</label>
          <select
            value={climate}
            onChange={(e) => setClimate(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
          >
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="cold">Cold</option>
            <option value="hot">Hot</option>
          </select>
        </div>

        {/* Current System */}
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-2">Current System</label>
          <select
            value={currentSystem}
            onChange={(e) => setCurrentSystem(e.target.value)}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-slate-900"
          >
            <option value="new">New (< 5 years)</option>
            <option value="old">Old (> 10 years)</option>
            <option value="none">No System</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div className="mt-8 pt-6 border-t-2 border-blue-300 space-y-4">
        <div className="bg-white rounded-lg p-4">
          <p className="text-slate-600 text-sm">Estimated System Cost</p>
          <p className="text-3xl font-bold text-blue-600">${estimatedCost.toLocaleString()}</p>
        </div>

        <div className="bg-white rounded-lg p-4">
          <p className="text-slate-600 text-sm">Monthly Savings</p>
          <p className="text-3xl font-bold text-green-600">${estimatedSavings}</p>
        </div>

        <button
          onClick={() => onCalculate?.(estimatedCost)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition"
        >
          Get Free Quote
        </button>
      </div>
    </div>
  );
};

