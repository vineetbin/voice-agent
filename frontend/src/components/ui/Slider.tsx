/**
 * Slider component for numeric range inputs.
 */

import { forwardRef, type InputHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
  showValue?: boolean;
  valueFormatter?: (value: number) => string;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      className,
      label,
      description,
      showValue = true,
      valueFormatter = (v) => v.toString(),
      value,
      min = 0,
      max = 100,
      step = 1,
      id,
      ...props
    },
    ref
  ) => {
    const sliderId = id || label?.toLowerCase().replace(/\s+/g, '-');
    const numericValue = typeof value === 'string' ? parseFloat(value) : (value as number) || 0;
    const percentage = ((numericValue - Number(min)) / (Number(max) - Number(min))) * 100;

    return (
      <div className={clsx('w-full', className)}>
        <div className="flex items-center justify-between mb-2">
          {label && (
            <label
              htmlFor={sliderId}
              className="text-sm font-medium text-gray-700"
            >
              {label}
            </label>
          )}
          {showValue && (
            <span className="text-sm font-medium text-indigo-600">
              {valueFormatter(numericValue)}
            </span>
          )}
        </div>
        <div className="relative">
          <input
            ref={ref}
            type="range"
            id={sliderId}
            value={value}
            min={min}
            max={max}
            step={step}
            className={twMerge(
              clsx(
                'w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer',
                'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2',
                '[&::-webkit-slider-thumb]:appearance-none',
                '[&::-webkit-slider-thumb]:w-4',
                '[&::-webkit-slider-thumb]:h-4',
                '[&::-webkit-slider-thumb]:bg-indigo-600',
                '[&::-webkit-slider-thumb]:rounded-full',
                '[&::-webkit-slider-thumb]:cursor-pointer',
                '[&::-webkit-slider-thumb]:transition-transform',
                '[&::-webkit-slider-thumb]:hover:scale-110',
                '[&::-moz-range-thumb]:w-4',
                '[&::-moz-range-thumb]:h-4',
                '[&::-moz-range-thumb]:bg-indigo-600',
                '[&::-moz-range-thumb]:rounded-full',
                '[&::-moz-range-thumb]:cursor-pointer',
                '[&::-moz-range-thumb]:border-0'
              )
            )}
            style={{
              background: `linear-gradient(to right, rgb(79 70 229) ${percentage}%, rgb(229 231 235) ${percentage}%)`,
            }}
            {...props}
          />
        </div>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
      </div>
    );
  }
);

Slider.displayName = 'Slider';

