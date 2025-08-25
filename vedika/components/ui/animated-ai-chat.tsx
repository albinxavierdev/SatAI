"use client";

import { useEffect, useRef, useCallback, useMemo, useState, forwardRef } from "react";
import { cn } from "@/lib/utils";
import {
    ImageIcon,
    Figma,
    MonitorIcon,
    SendIcon,
    XIcon,
    LoaderIcon,
    Sparkles,
    Command,
    RefreshCw,
    Bot,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { apiClient } from "@/lib/api";
import { ChatMessage, type ChatMessage as ChatMessageType } from "./chat-message";

interface UseAutoResizeTextareaProps {
    minHeight: number;
    maxHeight?: number;
}

function useAutoResizeTextarea({
    minHeight,
    maxHeight,
}: UseAutoResizeTextareaProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const adjustHeight = useCallback(
        (reset?: boolean) => {
            const textarea = textareaRef.current;
            if (!textarea) return;

            if (reset) {
                textarea.style.height = `${minHeight}px`;
                return;
            }

            textarea.style.height = `${minHeight}px`;
            const newHeight = Math.max(
                minHeight,
                Math.min(
                    textarea.scrollHeight,
                    maxHeight ?? Number.POSITIVE_INFINITY
                )
            );

            textarea.style.height = `${newHeight}px`;
        },
        [minHeight, maxHeight]
    );

    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = `${minHeight}px`;
        }
    }, [minHeight]);

    useEffect(() => {
        const handleResize = () => adjustHeight();
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, [adjustHeight]);

    return { textareaRef, adjustHeight };
}

interface CommandSuggestion {
    icon: React.ReactNode;
    label: string;
    description: string;
    prefix: string;
}

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  containerClassName?: string;
  showRing?: boolean;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, containerClassName, showRing = true, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    
    return (
      <div className={cn(
        "relative",
        containerClassName
      )}>
        <textarea
          className={cn(
            "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
            "transition-all duration-200 ease-in-out",
            "placeholder:text-muted-foreground",
            "disabled:cursor-not-allowed disabled:opacity-50",
            showRing ? "focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0" : "",
            className
          )}
          ref={ref}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />
        
        {showRing && isFocused && (
          <motion.span 
            className="absolute inset-0 rounded-md pointer-events-none ring-2 ring-offset-0 ring-violet-500/30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        )}

        {props.onChange && (
          <div 
            className="absolute bottom-2 right-2 opacity-0 w-2 h-2 bg-violet-500 rounded-full"
            style={{
              animation: 'none',
            }}
            id="textarea-ripple"
          />
        )}
      </div>
    )
  }
)
Textarea.displayName = "Textarea"

export function AnimatedAIChat() {
    const [value, setValue] = useState("");
    const [activeSuggestion, setActiveSuggestion] = useState<number>(-1);
    const [showCommandPalette, setShowCommandPalette] = useState(false);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
    const [messages, setMessages] = useState<ChatMessageType[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { textareaRef, adjustHeight } = useAutoResizeTextarea({
        minHeight: 60,
        maxHeight: 200,
    });
    const [inputFocused, setInputFocused] = useState(false);
    const commandPaletteRef = useRef<HTMLDivElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const commandSuggestions = useMemo<CommandSuggestion[]>(() => [
        { 
            icon: <Sparkles className="w-4 h-4" />, 
            label: "Chandrayaan", 
            description: "Learn about Chandrayaan missions", 
            prefix: "/chandrayaan" 
        },
        { 
            icon: <MonitorIcon className="w-4 h-4" />, 
            label: "Satellites", 
            description: "Explore ISRO satellites", 
            prefix: "/satellites" 
        },
        { 
            icon: <ImageIcon className="w-4 h-4" />, 
            label: "Launch Vehicles", 
            description: "Learn about rockets", 
            prefix: "/launchers" 
        },
        { 
            icon: <Figma className="w-4 h-4" />, 
            label: "ISRO Centres", 
            description: "Explore ISRO facilities", 
            prefix: "/centres" 
        },
    ], []);

    useEffect(() => {
        if (value.startsWith('/') && !value.includes(' ')) {
            setShowCommandPalette(true);
            
            const matchingSuggestionIndex = commandSuggestions.findIndex(
                (cmd) => cmd.prefix.startsWith(value)
            );
            
            if (matchingSuggestionIndex >= 0) {
                setActiveSuggestion(matchingSuggestionIndex);
            } else {
                setActiveSuggestion(-1);
            }
        } else {
            setShowCommandPalette(false);
        }
    }, [value, commandSuggestions]);

    useEffect(() => {
        // Add welcome message
        if (messages.length === 0) {
            setMessages([{
                id: 'welcome',
                type: 'assistant',
                content: 'Hello! I\'m Vedika, your ISRO knowledge assistant. I can help you with information about Indian satellites, spacecraft, launch vehicles, and space missions. What would you like to know?',
                timestamp: new Date(),
            }]);
        }
    }, [messages.length]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            setMousePosition({ x: e.clientX, y: e.clientY });
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, []);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as Node;
            const commandButton = document.querySelector('[data-command-button]');
            
            if (commandPaletteRef.current && 
                !commandPaletteRef.current.contains(target) && 
                !commandButton?.contains(target)) {
                setShowCommandPalette(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (showCommandPalette) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setActiveSuggestion(prev => 
                    prev < commandSuggestions.length - 1 ? prev + 1 : 0
                );
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setActiveSuggestion(prev => 
                    prev > 0 ? prev - 1 : commandSuggestions.length - 1
                );
            } else if (e.key === 'Tab' || e.key === 'Enter') {
                e.preventDefault();
                if (activeSuggestion >= 0) {
                    const selectedCommand = commandSuggestions[activeSuggestion];
                    setValue(selectedCommand.prefix + ' ');
                    setShowCommandPalette(false);
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                setShowCommandPalette(false);
            }
        } else if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (value.trim()) {
                handleSendMessage();
            }
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async () => {
        if (value.trim() && !isLoading) {
            const userMessage: ChatMessageType = {
                id: Date.now().toString(),
                type: 'user',
                content: value.trim(),
                timestamp: new Date(),
            };

            setMessages(prev => [...prev, userMessage]);
            setValue("");
            adjustHeight(true);
            setIsLoading(true);
            setError(null);

            try {
                const response = await apiClient.query({
                    query: userMessage.content,
                    max_results: 5,
                    include_metadata: true,
                });

                const assistantMessage: ChatMessageType = {
                    id: (Date.now() + 1).toString(),
                    type: 'assistant',
                    content: response.answer,
                    timestamp: new Date(),
                    metadata: {
                        relevant_documents: response.relevant_documents,
                        model_used: response.model_used,
                    },
                };

                setMessages(prev => [...prev, assistantMessage]);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to get response');
                console.error('Error sending message:', err);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const selectCommandSuggestion = (index: number) => {
        const selectedCommand = commandSuggestions[index];
        let query = '';
        
        switch (selectedCommand.prefix) {
            case '/chandrayaan':
                query = 'Tell me about Chandrayaan missions';
                break;
            case '/satellites':
                query = 'What satellites has ISRO launched?';
                break;
            case '/launchers':
                query = 'What launch vehicles does ISRO use?';
                break;
            case '/centres':
                query = 'What are the main ISRO centres and facilities?';
                break;
            default:
                query = selectedCommand.prefix + ' ';
        }
        
        setValue(query);
        setShowCommandPalette(false);
    };

    const clearChat = () => {
        setMessages([{
            id: 'welcome',
            type: 'assistant',
            content: 'Hello! I\'m Vedika, your ISRO knowledge assistant. I can help you with information about Indian satellites, spacecraft, launch vehicles, and space missions. What would you like to know?',
            timestamp: new Date(),
        }]);
        setError(null);
    };

    return (
        <div className="min-h-screen flex flex-col w-full bg-transparent text-white relative overflow-hidden">
            <div className="absolute inset-0 w-full h-full overflow-hidden">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
                <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
                <div className="absolute top-1/4 right-1/3 w-64 h-64 bg-fuchsia-500/10 rounded-full mix-blend-normal filter blur-[96px] animate-pulse delay-1000" />
            </div>
            
            <div className="w-full max-w-6xl mx-auto relative h-screen flex flex-col">
                <motion.div 
                    className="relative z-10 flex flex-col h-full"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                >
                    {/* Header */}
                    <div className="text-center space-y-3 py-6">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2, duration: 0.5 }}
                            className="inline-block"
                        >
                            <h1 className="text-4xl font-medium tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white/90 to-white/40 pb-1">
                                Vedika - ISRO Knowledge Assistant
                            </h1>
                            <motion.div 
                                className="h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"
                                initial={{ width: 0, opacity: 0 }}
                                animate={{ width: "100%", opacity: 1 }}
                                transition={{ delay: 0.5, duration: 0.8 }}
                            />
                        </motion.div>
                        <motion.p 
                            className="text-sm text-white/40"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 }}
                        >
                            Ask me anything about ISRO satellites, spacecraft, and space missions
                        </motion.p>
                    </div>

                    {/* Chat Messages */}
                    <motion.div 
                        className="flex-1 overflow-y-auto space-y-2 px-4 min-h-0"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        {messages.map((message) => (
                            <ChatMessage 
                                key={message.id} 
                                message={message} 
                            />
                        ))}
                        {isLoading && (
                            <motion.div 
                                className="flex gap-3 p-4 justify-start"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-violet-400" />
                                </div>
                                <div className="bg-white/[0.05] rounded-2xl px-4 py-3 text-sm text-white/60 border border-white/[0.05]">
                                    <div className="flex items-center gap-2">
                                        <LoaderIcon className="w-4 h-4 animate-spin" />
                                        <span>Thinking...</span>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                        {error && (
                            <motion.div 
                                className="flex gap-3 p-4 justify-start"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                            >
                                <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center">
                                    <XIcon className="w-4 h-4 text-red-400" />
                                </div>
                                <div className="bg-red-500/10 rounded-2xl px-4 py-3 text-sm text-red-400 border border-red-500/20">
                                    <div className="flex items-center gap-2">
                                        <span>Error: {error}</span>
                                        <button 
                                            onClick={() => setError(null)}
                                            className="ml-2 text-red-300 hover:text-red-200"
                                        >
                                            <XIcon className="w-3 h-3" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                        <div ref={messagesEndRef} />
                    </motion.div>

                    {/* Input Section - Fixed at Bottom */}
                    <div className="mt-auto pt-6">
                        <motion.div 
                            className="relative backdrop-blur-2xl bg-white/[0.02] rounded-2xl border border-white/[0.05] shadow-2xl mx-4"
                            initial={{ scale: 0.98 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.1 }}
                        >
                            <AnimatePresence>
                                {showCommandPalette && (
                                    <motion.div 
                                        ref={commandPaletteRef}
                                        className="absolute left-4 right-4 bottom-full mb-2 backdrop-blur-xl bg-black/90 rounded-lg z-50 shadow-lg border border-white/10 overflow-hidden"
                                        initial={{ opacity: 0, y: 5 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 5 }}
                                        transition={{ duration: 0.15 }}
                                    >
                                        <div className="py-1 bg-black/95">
                                            {commandSuggestions.map((suggestion, index) => (
                                                <motion.div
                                                    key={suggestion.prefix}
                                                    className={cn(
                                                        "flex items-center gap-2 px-3 py-2 text-xs transition-colors cursor-pointer",
                                                        activeSuggestion === index 
                                                            ? "bg-white/10 text-white" 
                                                            : "text-white/70 hover:bg-white/5"
                                                    )}
                                                    onClick={() => selectCommandSuggestion(index)}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ delay: index * 0.03 }}
                                                >
                                                    <div className="w-5 h-5 flex items-center justify-center text-white/60">
                                                        {suggestion.icon}
                                                    </div>
                                                    <div className="font-medium">{suggestion.label}</div>
                                                    <div className="text-white/40 text-xs ml-1">
                                                        {suggestion.prefix}
                                                    </div>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <div className="p-4">
                                <Textarea
                                    ref={textareaRef}
                                    value={value}
                                    onChange={(e) => {
                                        setValue(e.target.value);
                                        adjustHeight();
                                    }}
                                    onKeyDown={handleKeyDown}
                                    onFocus={() => setInputFocused(true)}
                                    onBlur={() => setInputFocused(false)}
                                    placeholder="Ask me about ISRO satellites, spacecraft, or space missions..."
                                    containerClassName="w-full"
                                    className={cn(
                                        "w-full px-4 py-3",
                                        "resize-none",
                                        "bg-transparent",
                                        "border-none",
                                        "text-white/90 text-sm",
                                        "focus:outline-none",
                                        "placeholder:text-white/20",
                                        "min-h-[60px]"
                                    )}
                                    style={{
                                        overflow: "hidden",
                                    }}
                                    showRing={false}
                                />
                            </div>

                            <div className="p-4 border-t border-white/[0.05] flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <motion.button
                                        type="button"
                                        onClick={clearChat}
                                        whileTap={{ scale: 0.94 }}
                                        className="p-2 text-white/40 hover:text-white/90 rounded-lg transition-colors relative group"
                                        title="Clear chat"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        <motion.span
                                            className="absolute inset-0 bg-white/[0.05] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                                            layoutId="button-highlight"
                                        />
                                    </motion.button>
                                    <motion.button
                                        type="button"
                                        data-command-button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setShowCommandPalette(prev => !prev);
                                        }}
                                        whileTap={{ scale: 0.94 }}
                                        className={cn(
                                            "p-2 text-white/40 hover:text-white/90 rounded-lg transition-colors relative group",
                                            showCommandPalette && "bg-white/10 text-white/90"
                                        )}
                                        title="Quick commands"
                                    >
                                        <Command className="w-4 h-4" />
                                        <motion.span
                                            className="absolute inset-0 bg-white/[0.05] rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                                            layoutId="button-highlight"
                                        />
                                    </motion.button>
                                </div>
                                
                                <motion.button
                                    type="button"
                                    onClick={handleSendMessage}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.98 }}
                                    disabled={isLoading || !value.trim()}
                                    className={cn(
                                        "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                                        "flex items-center gap-2",
                                        value.trim()
                                            ? "bg-white text-[#0A0A0B] shadow-lg shadow-white/10"
                                            : "bg-white/[0.05] text-white/40"
                                    )}
                                >
                                    {isLoading ? (
                                        <LoaderIcon className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <SendIcon className="w-4 h-4" />
                                    )}
                                    <span>Send</span>
                                </motion.button>
                            </div>
                        </motion.div>

                        {/* Quick Command Suggestions */}
                        <div className="flex flex-wrap items-center justify-center gap-3 py-6 pb-8">
                            {commandSuggestions.map((suggestion, index) => (
                                <motion.button
                                    key={suggestion.prefix}
                                    onClick={() => selectCommandSuggestion(index)}
                                    className="flex items-center gap-2 px-4 py-3 bg-white/[0.03] hover:bg-white/[0.08] rounded-xl text-sm text-white/70 hover:text-white/90 transition-all relative group border border-white/[0.05] hover:border-white/[0.1] backdrop-blur-sm"
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                >
                                    <div className="text-violet-400">
                                        {suggestion.icon}
                                    </div>
                                    <span className="font-medium">{suggestion.label}</span>
                                    <motion.div
                                        className="absolute inset-0 border border-white/[0.05] rounded-xl"
                                        initial={false}
                                        animate={{
                                            opacity: [0, 1],
                                            scale: [0.98, 1],
                                        }}
                                        transition={{
                                            duration: 0.3,
                                            ease: "easeOut",
                                        }}
                                    />
                                </motion.button>
                            ))}
                        </div>
                    </div>
                </motion.div>
            </div>

            {inputFocused && (
                <motion.div 
                    className="fixed w-[50rem] h-[50rem] rounded-full pointer-events-none z-0 opacity-[0.02] bg-gradient-to-r from-violet-500 via-fuchsia-500 to-indigo-500 blur-[96px]"
                    animate={{
                        x: mousePosition.x - 400,
                        y: mousePosition.y - 400,
                    }}
                    transition={{
                        type: "spring",
                        damping: 25,
                        stiffness: 150,
                        mass: 0.5,
                    }}
                />
            )}
        </div>
    );
}






