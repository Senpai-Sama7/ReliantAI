import React, { useState } from 'react';

interface Testimonial {
  id: string;
  name: string;
  title: string;
  content: string;
  rating: number;
  image?: string;
  video?: string;
}

interface TestimonialsProps {
  testimonials: Testimonial[];
}

export const Testimonials: React.FC<TestimonialsProps> = ({ testimonials }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const next = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const prev = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  if (!testimonials.length) return null;

  const current = testimonials[currentIndex];

  return (
    <div className="bg-slate-50 rounded-lg p-8 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-slate-900">Customer Stories</h2>
        <div className="flex gap-2">
          <button
            onClick={prev}
            className="p-2 hover:bg-slate-200 rounded-full transition"
          >
            ←
          </button>
          <button
            onClick={next}
            className="p-2 hover:bg-slate-200 rounded-full transition"
          >
            →
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {current.image && (
          <img
            src={current.image}
            alt={current.name}
            className="w-16 h-16 rounded-full object-cover"
          />
        )}

        <div className="flex gap-1">
          {Array.from({ length: current.rating }).map((_, i) => (
            <span key={i} className="text-yellow-400">★</span>
          ))}
        </div>

        <p className="text-slate-700 italic leading-relaxed">"{current.content}"</p>

        <div>
          <p className="font-semibold text-slate-900">{current.name}</p>
          <p className="text-sm text-slate-600">{current.title}</p>
        </div>
      </div>

      <div className="flex gap-2 mt-6">
        {testimonials.map((_, i) => (
          <button
            key={i}
            onClick={() => setCurrentIndex(i)}
            className={`w-2 h-2 rounded-full transition ${
              i === currentIndex ? 'bg-blue-600 w-6' : 'bg-slate-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
};
