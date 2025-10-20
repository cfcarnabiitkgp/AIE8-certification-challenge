'use client';

import React, { useState, useCallback } from 'react';
import { SuggestionType } from '@/types';
import { Filter } from 'lucide-react';

interface EditorProps {
  value: string;
  onChange: (value: string) => void;
  onTriggerReview: () => void;
  selectedTypes: SuggestionType[];
  onToggleType: (type: SuggestionType) => void;
  filterSeverity: 'all' | 'error' | 'warning' | 'info';
  onFilterSeverityChange: (severity: 'all' | 'error' | 'warning' | 'info') => void;
}

const Editor: React.FC<EditorProps> = ({
  value,
  onChange,
  onTriggerReview,
  selectedTypes,
  onToggleType,
  filterSeverity,
  onFilterSeverityChange
}) => {
  const [lineCount, setLineCount] = useState(1);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
    setLineCount(newValue.split('\n').length);
  }, [onChange]);

  const analysisTypes: { type: SuggestionType; label: string }[] = [
    { type: 'clarity', label: 'Clarity' },
    { type: 'rigor', label: 'Rigor' },
  ];

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="border-b px-4 py-3 bg-gray-50">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800">Markdown Editor</h2>
          <button
            onClick={onTriggerReview}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            Review Paper
          </button>
        </div>

        {/* Unified Filter Panel */}
        <div className="space-y-3 p-3 bg-white rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </div>

          {/* Analysis Type Selection */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              Analysis Types
            </label>
            <div className="flex flex-wrap gap-2">
              {analysisTypes.map(({ type, label }) => (
                <label
                  key={type}
                  className="flex items-center gap-1.5 cursor-pointer text-sm px-3 py-1.5 rounded border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={() => onToggleType(type)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Severity Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">
              Severity Filter
            </label>
            <select
              value={filterSeverity}
              onChange={(e) => onFilterSeverityChange(e.target.value as 'all' | 'error' | 'warning' | 'info')}
              className="w-full text-sm border rounded px-3 py-1.5 bg-white text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Severities</option>
              <option value="error">Errors Only</option>
              <option value="warning">Warnings Only</option>
              <option value="info">Info Only</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-12 bg-gray-100 border-r overflow-y-auto">
          <div className="text-right pr-2 py-4 text-xs text-gray-500 font-mono select-none">
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i + 1} className="leading-6">
                {i + 1}
              </div>
            ))}
          </div>
        </div>
        <textarea
          value={value}
          onChange={handleChange}
          className="flex-1 p-4 resize-none focus:outline-none markdown-editor text-gray-800"
          placeholder="# Research Paper Title

## Abstract

Write your abstract here...

## Introduction

Start writing your research paper in Markdown format. The AI will provide suggestions as you write.

## Related Work

## Methodology

## Results

## Conclusion

## References
"
          spellCheck={false}
        />
      </div>
    </div>
  );
};

export default Editor;

