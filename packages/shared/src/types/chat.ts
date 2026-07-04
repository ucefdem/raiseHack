export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  agentId: string;
  conversationId?: string;
  message: string;
  context?: {
    departmentId?: string;
    departmentName?: string;
  };
}

export interface ChatResponse {
  conversationId: string;
  message: ChatMessage;
}

export interface Conversation {
  id: string;
  agentId: string;
  userId: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}
