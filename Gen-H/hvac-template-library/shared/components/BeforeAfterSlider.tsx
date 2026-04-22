import React, { useState } from 'react';

interface BeforeAfterSliderProps {
  beforeImage: string;
  afterImage: string;
  beforeLabel?: string;
  afterLabel?: string;
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeImage,
  afterImage,
  beforeLabel = 'Before',
  afterLabel = 'After',
}) => {
  const [sliderPosition, setSliderPosition] = useState(50);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const newPosition = ((e.clientX - rect.left) / rect.width) * 100;
    setSliderPosition(Math.max(0, Math.min(100, newPosition)));
  };

  return (
    <div
      className="relative w-full max-w-2xl mx-auto overflow-hidden rounded-lg"
      onMouseMove={handleMouseMove}
      style={{ cursor: 'col-resize' }}
    >
      <img src={beforeImage} alt={beforeLabel} className="w-full block" />

      <div
        className="absolute top-0 left-0 w-full h-full overflow-hidden"
        style={{ width: `${sliderPosition}%` }}
      >
        <img src={afterImage} alt={afterLabel} className="w-full h-full object-cover block" />
      </div>

      <div
        className="absolute top-0 left-0 w-1 h-full bg-white shadow-lg"
        style={{ left: `${sliderPosition}%` }}
      >
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-full p-2">
          <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M15 19l-7-7 7-7" stroke="currentColor" strokeWidth="2" fill="none" />
            <path d="M9 19l7-7-7-7" stroke="currentColor" strokeWidth="2" fill="none" />
          </svg>
        </div>
      </div>

      <div className="absolute top-4 left-4 bg-black bg-opacity-50 text-white px-4 py-2 rounded">
        {beforeLabel}
      </div>
      <div className="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-4 py-2 rounded">
        {afterLabel}
      </div>
    </div>
  );
};

