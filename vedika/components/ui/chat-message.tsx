import { motion } from "framer-motion";
import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    relevant_documents?: Array<{
      content: string;
      distance: number;
      metadata?: {
        record_name?: string;
        source_file?: string;
        [key: string]: unknown;
      };
    }>;
    model_used?: string;
  };
}

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user';
  
  return (
    <motion.div
      className={cn(
        "flex gap-3 p-4",
        isUser ? "justify-end" : "justify-start"
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
          <Bot className="w-4 h-4 text-violet-400" />
        </div>
      )}
      
      <div className={cn(
        "max-w-[80%] space-y-3",
        isUser ? "text-right" : "text-left"
      )}>
        <div className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser 
            ? "bg-white text-[#0A0A0B] ml-auto" 
            : "bg-white/[0.05] text-white/90 border border-white/[0.05]"
        )}>
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
        
        {!isUser && message.metadata?.relevant_documents && (
          <div className="space-y-3">
            <div className="text-xs text-white/40 px-1 font-medium">
              📚 Sources ({message.metadata.relevant_documents.length})
            </div>
            {message.metadata.relevant_documents.slice(0, 3).map((doc, index) => (
              <motion.div
                key={index}
                className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.08] text-xs backdrop-blur-sm"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-violet-400 rounded-full"></div>
                  <div className="text-white/80 font-medium">
                    {(typeof doc.metadata?.record_name === 'string' ? doc.metadata.record_name : null) || `Document ${index + 1}`}
                  </div>
                </div>
                <div className="text-white/60 leading-relaxed mb-2">
                  {doc.content}
                </div>
                {doc.metadata?.source_file && typeof doc.metadata.source_file === 'string' && (
                  <div className="flex items-center gap-2 text-white/40 text-xs">
                    <span className="opacity-60">📄</span>
                    <span>{doc.metadata.source_file}</span>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
        
        <div className={cn(
          "text-xs text-white/30 flex items-center gap-2",
          isUser ? "justify-end" : "justify-start"
        )}>
          <span className="opacity-60">🕐</span>
          {message.timestamp.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
      
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
          <User className="w-4 h-4 text-white/60" />
        </div>
      )}
    </motion.div>
  );
}
