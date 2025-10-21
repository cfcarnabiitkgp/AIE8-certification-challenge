'use client';

import React, { useState, useCallback } from 'react';
import Editor from '@/components/Editor';
import SuggestionPanel from '@/components/SuggestionPanel';
import { Suggestion, ReviewRequest, ReviewResponse, SuggestionType } from '@/types';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [content, setContent] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [selectedTypes, setSelectedTypes] = useState<SuggestionType[]>(['clarity', 'rigor']);
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'error' | 'warning' | 'info'>('all');

  const handleReview = useCallback(async () => {
    if (!content.trim()) {
      alert('Please write some content before reviewing.');
      return;
    }

    if (selectedTypes.length === 0) {
      alert('Please select at least one analysis type');
      return;
    }

    setIsLoading(true);
    setSuggestions([]);

    try {
      const request: ReviewRequest = {
        content,
        session_id: sessionId,
        target_venue: 'general academic journal',
        analysis_types: selectedTypes,
      };

      const response = await axios.post<ReviewResponse>(
        `${API_URL}/api/review/analyze`,
        request,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('API Response:', response.data);
      console.log('Suggestions received:', response.data.suggestions);
      console.log('Number of suggestions:', response.data.suggestions?.length);
      console.log('Analysis types requested:', selectedTypes);
      setSuggestions(response.data.suggestions);
      console.log(`Review completed in ${response.data.processing_time.toFixed(2)}s`);
    } catch (error) {
      console.error('Error during review:', error);
      alert('Error analyzing paper. Please check the console and ensure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  }, [content, sessionId, selectedTypes]);

  const toggleType = (type: SuggestionType) => {
    setSelectedTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-blue-600 text-white py-4 px-6 shadow-md">
        <h1 className="text-2xl font-bold">Peerly: An agentic co-reviewer for technical manuscripts</h1>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <div className="w-1/2 border-r">
          <Editor
            value={content}
            onChange={setContent}
            onTriggerReview={handleReview}
            selectedTypes={selectedTypes}
            onToggleType={toggleType}
            filterSeverity={filterSeverity}
            onFilterSeverityChange={setFilterSeverity}
          />
        </div>

        <div className="w-1/2">
          <SuggestionPanel
            suggestions={suggestions}
            isLoading={isLoading}
            filterSeverity={filterSeverity}
          />
        </div>
      </main>
    </div>
  );
}

