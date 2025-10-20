export type SuggestionType = 
  | 'clarity' 
  | 'rigor' 
  | 'coherence' 
  | 'citation' 
  | 'best_practices' 
  | 'structure';

export type SeverityLevel = 'info' | 'warning' | 'error';

export interface Suggestion {
  id: string;
  type: SuggestionType;
  severity: SeverityLevel;
  title: string;
  description: string;
  section: string;
  line_start?: number;
  line_end?: number;
  suggested_fix?: string;
  references: string[];
}

export interface ReviewRequest {
  content: string;
  session_id: string;
  target_venue?: string;
  analysis_types: string[];
}

export interface ReviewResponse {
  suggestions: Suggestion[];
  session_id: string;
  processing_time: number;
}

