'use client';

import React from 'react';
import { Suggestion, SuggestionType } from '@/types';
import { AlertCircle, Info, AlertTriangle, CheckCircle } from 'lucide-react';

interface SuggestionPanelProps {
  suggestions: Suggestion[];
  isLoading: boolean;
  filterSeverity: 'all' | 'error' | 'warning' | 'info';
}

const SuggestionPanel: React.FC<SuggestionPanelProps> = ({ suggestions, isLoading, filterSeverity }) => {
  // Debug logging
  React.useEffect(() => {
    console.log('SuggestionPanel - suggestions prop:', suggestions);
    console.log('SuggestionPanel - suggestions length:', suggestions?.length);
    console.log('SuggestionPanel - isLoading:', isLoading);
  }, [suggestions, isLoading]);

  const filteredSuggestions = suggestions.filter(s => {
    const severityMatch = filterSeverity === 'all' || s.severity === filterSeverity;
    return severityMatch;
  });

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'info':
        return <Info className="w-5 h-5 text-blue-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getTypeLabel = (type: SuggestionType) => {
    return type.split('_').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getTypeColor = (type: SuggestionType) => {
    const colors: Record<SuggestionType, string> = {
      clarity: 'bg-purple-100 text-purple-800',
      rigor: 'bg-green-100 text-green-800',
      coherence: 'bg-blue-100 text-blue-800',
      citation: 'bg-yellow-100 text-yellow-800',
      best_practices: 'bg-indigo-100 text-indigo-800',
      structure: 'bg-pink-100 text-pink-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      <div className="border-b px-4 py-3 bg-white">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Suggestions</h2>
          {suggestions.length > 0 && (
            <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
              {filteredSuggestions.length} of {suggestions.length}
            </span>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="flex flex-col items-center gap-2">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="text-sm text-gray-600">Analyzing paper...</p>
            </div>
          </div>
        ) : filteredSuggestions.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-gray-500">
            <div className="text-center">
              {suggestions.length === 0 ? (
                <>
                  <CheckCircle className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                  <p>No suggestions yet</p>
                  <p className="text-sm mt-1">Click "Review Paper" to get feedback</p>
                </>
              ) : (
                <p>No suggestions match the current filters</p>
              )}
            </div>
          </div>
        ) : (
          filteredSuggestions.map((suggestion) => (
            <div
              key={suggestion.id}
              className={`suggestion-card p-4 rounded-lg border-l-4 ${getSeverityColor(suggestion.severity)} shadow-sm`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {getSeverityIcon(suggestion.severity)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-semibold text-gray-900 text-sm">
                      {suggestion.title}
                    </h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ${getTypeColor(suggestion.type)}`}>
                      {getTypeLabel(suggestion.type)}
                    </span>
                  </div>

                  <p className="text-sm text-gray-700 mb-2">
                    {suggestion.description}
                  </p>

                  <div className="text-xs text-gray-600 mb-2">
                    <span className="font-medium">Section:</span> {suggestion.section}
                    {suggestion.line_start && (
                      <span className="ml-2">
                        <span className="font-medium">Lines:</span> {suggestion.line_start}
                        {suggestion.line_end && suggestion.line_end !== suggestion.line_start && `-${suggestion.line_end}`}
                      </span>
                    )}
                  </div>

                  {suggestion.suggested_fix && (
                    <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                      <p className="text-xs font-medium text-gray-700 mb-1">Suggested Fix:</p>
                      <p className="text-xs text-gray-600">{suggestion.suggested_fix}</p>
                    </div>
                  )}

                  {suggestion.references && suggestion.references.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-700 mb-1">References:</p>
                      <ul className="text-xs text-gray-600 space-y-1">
                        {suggestion.references.slice(0, 2).map((ref, idx) => (
                          <li key={idx} className="truncate">• {ref}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default SuggestionPanel;

