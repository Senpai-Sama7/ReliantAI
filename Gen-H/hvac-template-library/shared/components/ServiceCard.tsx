import React from 'react';

interface ServiceCardProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  image?: string;
  features?: string[];
}

export const ServiceCard: React.FC<ServiceCardProps> = ({
  title,
  description,
  icon,
  image,
  features,
}) => {
  return (
    <div className="bg-white rounded-lg shadow-lg hover:shadow-xl transition overflow-hidden group">
      {image && (
        <div className="overflow-hidden h-48">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
          />
        </div>
      )}
      <div className="p-6">
        {icon && <div className="text-4xl mb-4">{icon}</div>}
        <h3 className="text-xl font-bold text-slate-900 mb-2">{title}</h3>
        <p className="text-slate-600 mb-4">{description}</p>
        {features && (
          <ul className="space-y-2">
            {features.map((feature, i) => (
              <li key={i} className="flex items-center text-sm text-slate-700">
                <span className="w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
                {feature}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

