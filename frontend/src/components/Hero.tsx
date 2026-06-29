"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Play,
  Pause,
  RotateCcw,
  Brain,
  Volume2,
  Target,
  Smile,
  Zap,
  Activity,
  CheckCircle,
  Sparkles,
  ChevronRight
} from "lucide-react";
import Link from "next/link";

interface Turn {
  speaker: "agent" | "user";
  text: string;
  correction?: string;
  goal: string;
  successCriteria: string[];
  episodicMemory: string[];
  workingMemory: Record<string, string | number>;
  confidence: number;
  sentiment: string;
  frustrationSlope: string;
}

interface Scenario {
  name: string;
  lang: string;
  flag: string;
  title: string;
  turns: Turn[];
}

const scenarios: Scenario[] = [
  {
    name: "EMI Collection",
    lang: "Hindi / हिन्दी",
    flag: "🇮🇳",
    title: "Debt Collection & Negotiation",
    turns: [
      {
        speaker: "agent",
        text: "नमस्ते, मैं वोइस एआई से बात कर रही हूँ। क्या मैं अमित कुमार जी से बात कर सकती हूँ?",
        goal: "Confirm customer identity",
        successCriteria: ["User confirms identity == true"],
        episodicMemory: ["Initiated EMI collection call"],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", month: "April" },
        confidence: 99,
        sentiment: "Empathetic / Professional",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "हाँ बोलिए, अमित बात कर रहा हूँ। क्या बात है?",
        goal: "Confirm customer identity",
        successCriteria: ["User confirms identity == true"],
        episodicMemory: ["Initiated EMI collection call", "Identity confirmed: Amit Kumar"],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", month: "April" },
        confidence: 97,
        sentiment: "Neutral / Inquisitive",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "अमित जी, मैं आपकी ₹15,000 की अप्रैल महीने की ईएमआई भुगतान के संबंध में याद दिलाने के लिए कॉल कर रही हूँ। क्या हम इसका भुगतान आज पूरा कर सकते हैं?",
        goal: "Collect payment confirmation",
        successCriteria: ["User confirms payment == true"],
        episodicMemory: ["Identity confirmed: Amit Kumar", "Reminded EMI: ₹15,000"],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", month: "April" },
        confidence: 98,
        sentiment: "Helpful / Empathetic",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "अरे यार, अभी बहुत तंगी चल रही है, सैलरी नहीं आई। आज तो भुगतान नहीं हो पाएगा बिल्कुल भी।",
        goal: "Collect payment confirmation",
        successCriteria: ["User confirms payment == true"],
        episodicMemory: ["Identity confirmed: Amit Kumar", "User reports financial stress / no salary"],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", month: "April", obstacle: "Salary delayed" },
        confidence: 94,
        sentiment: "Stressed / Defensive",
        frustrationSlope: "Rising (+0.2)"
      },
      {
        speaker: "agent",
        text: "मैं आपकी परिस्थिति समझ सकती हूँ, अमित जी। घबरेइए मत, हमारे पास दो विकल्प हैं। या तो हम इसे दो छोटी किस्तों में बाँट सकते हैं, या फिर भुगतान की अंतिम तारीख को 25 मई तक बढ़ा सकते हैं। आपके लिए क्या आसान रहेगा?",
        goal: "Negotiate alternative payment plan",
        successCriteria: ["User accepts installment == true", "User accepts extension == true"],
        episodicMemory: [
          "User reports financial stress",
          "Offered split EMI plan",
          "Offered extension to 25th May"
        ],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", month: "April", proposed_extension: "25th May" },
        confidence: 98,
        sentiment: "Highly Empathetic / Supportive",
        frustrationSlope: "Falling (-0.3)"
      },
      {
        speaker: "user",
        text: "अच्छा... अगर 25 मई तक का समय मिल जाए तो बहुत बढ़िया होगा। मैं 25 तारीख को पूरा दे दूँगा।",
        goal: "Negotiate alternative payment plan",
        successCriteria: ["User accepts extension == true"],
        episodicMemory: [
          "Offered extension to 25th May",
          "User agreed to extension on 25th May"
        ],
        workingMemory: { customer: "Amit Kumar", EMI: "₹15,000", promised_date: "25th May", method: "Full" },
        confidence: 96,
        sentiment: "Relieved / Cooperative",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "बहुत-बहुत धन्यवाद, अमित जी! मैंने आपकी भुगतान तारीख 25 मई के लिए बढ़ा दी है। आपके मोबाइल पर एक एसएमएस पुष्टिकरण लिंक भेजा गया है।",
        correction: "अपलोडिंग कन्फर्मेशन... आपकी नई देय तिथि 25 मई के लिए अपडेट हो गई है।",
        goal: "Wrap up call & trigger workflow",
        successCriteria: ["Schedule reminder SMS == true", "Update CRM == true"],
        episodicMemory: [
          "User agreed to extension on 25th May",
          "Updated CRM system",
          "Sent SMS confirmation link"
        ],
        workingMemory: { customer: "Amit Kumar", promised_date: "25th May", status: "Negotiated" },
        confidence: 99,
        sentiment: "Polite / Reassuring",
        frustrationSlope: "Negative (-0.5)"
      }
    ]
  },
  {
    name: "Lead Qualification",
    lang: "English",
    flag: "🇺🇸",
    title: "Real Estate Pre-Screening",
    turns: [
      {
        speaker: "agent",
        text: "Hi there! This is Voise Properties. I saw you requested details on our new 3-BHK villas. Are you looking to buy or rent?",
        goal: "Identify customer intent",
        successCriteria: ["Identify buyer/renter intent == true"],
        episodicMemory: ["Initiated real estate qualification"],
        workingMemory: { project: "Premium Villas", location: "Bangalore" },
        confidence: 99,
        sentiment: "Energetic / Friendly",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "Hey! Yes, I am actually looking to buy. I want to move in with my family within the next six months.",
        goal: "Identify customer intent",
        successCriteria: ["Identify buyer/renter intent == true"],
        episodicMemory: ["Buyer intent confirmed", "Timeline: 6 months"],
        workingMemory: { project: "Premium Villas", location: "Bangalore", intent: "Buy", timeline: "6 months" },
        confidence: 97,
        sentiment: "Interested / Direct",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "A 3-BHK villa for your family is a wonderful goal. To help me find the best fits, what is your preferred budget range?",
        goal: "Determine budget range",
        successCriteria: ["Budget range collected == true"],
        episodicMemory: ["Buyer intent confirmed", "Qualifying budget"],
        workingMemory: { project: "Premium Villas", location: "Bangalore", intent: "Buy", timeline: "6 months" },
        confidence: 98,
        sentiment: "Welcoming / Professional",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "My budget is around 1.5 to 2 Crores. I'd prefer something in Whitefield or Sarjapur.",
        goal: "Determine budget range",
        successCriteria: ["Budget range collected == true"],
        episodicMemory: ["Buyer intent confirmed", "Budget captured: ₹1.5 - 2Cr", "Locations: Whitefield/Sarjapur"],
        workingMemory: { project: "Premium Villas", intent: "Buy", budget: "₹1.5 - 2Cr", area: "Whitefield/Sarjapur" },
        confidence: 96,
        sentiment: "Decisive",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "Perfect budget range. We have two gorgeous options in Whitefield matching exactly what you described. Would you like to schedule a priority site visit this Saturday at 11 AM?",
        goal: "Book site visit in calendar",
        successCriteria: ["User books site visit == true"],
        episodicMemory: ["Captured budget and area", "Offered Saturday 11 AM slot"],
        workingMemory: { project: "Premium Villas", budget: "₹1.5 - 2Cr", area: "Whitefield", proposed_visit: "Saturday 11 AM" },
        confidence: 98,
        sentiment: "Proactive / Service-oriented",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "Yeah, actually Saturday at 11 AM works perfectly for me. Send me the location.",
        goal: "Book site visit in calendar",
        successCriteria: ["User books site visit == true"],
        episodicMemory: ["Confirmed Saturday 11 AM slot", "Site visit scheduled"],
        workingMemory: { project: "Premium Villas", budget: "₹1.5 - 2Cr", visit_scheduled: "Saturday 11:00 AM" },
        confidence: 99,
        sentiment: "Pleased / Satisfied",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "Excellent! I have booked your site visit for Saturday at 11 AM. An SMS with the location pin has been dispatched. Have a wonderful day!",
        goal: "Wrap up call & log lead",
        successCriteria: ["Dispatch SMS pin == true", "CRM log successful == true"],
        episodicMemory: ["Logged site visit in CRM", "Dispatched SMS location map"],
        workingMemory: { lead_status: "Qualified", action_required: "Sales follow-up" },
        confidence: 99,
        sentiment: "Friendly / Reassuring",
        frustrationSlope: "Negative (-0.4)"
      }
    ]
  },
  {
    name: "Appt. Booking",
    lang: "English",
    flag: "🏥",
    title: "Healthcare Inbound Booking",
    turns: [
      {
        speaker: "agent",
        text: "Good morning! You've reached MediCare Clinics. How can I help you today?",
        goal: "Identify caller intent",
        successCriteria: ["Caller intent identified == true"],
        episodicMemory: ["Inbound call received"],
        workingMemory: { clinic: "MediCare Clinics" },
        confidence: 99,
        sentiment: "Warm / Welcoming",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "Hi, I'd like to book an appointment with Dr. Sharma. It's been a while since my last checkup.",
        goal: "Identify caller intent",
        successCriteria: ["Caller intent identified == true"],
        episodicMemory: ["Caller wants appointment with Dr. Sharma"],
        workingMemory: { clinic: "MediCare Clinics", doctor: "Dr. Sharma", type: "Checkup" },
        confidence: 97,
        sentiment: "Friendly / Casual",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "Dr. Sharma has slots available tomorrow at 10 AM, 2 PM, or Thursday at 11 AM. Which works best for you?",
        goal: "Offer available slots",
        successCriteria: ["Slot preference captured == true"],
        episodicMemory: ["Caller wants Dr. Sharma", "Offered 3 available slots"],
        workingMemory: { doctor: "Dr. Sharma", slots: "Tomorrow 10 AM, 2 PM / Thu 11 AM" },
        confidence: 98,
        sentiment: "Helpful / Efficient",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "Tomorrow at 10 AM would be perfect.",
        goal: "Confirm slot selection",
        successCriteria: ["Slot confirmed == true"],
        episodicMemory: ["Caller selected tomorrow 10 AM"],
        workingMemory: { doctor: "Dr. Sharma", slot: "Tomorrow 10:00 AM" },
        confidence: 99,
        sentiment: "Decisive / Satisfied",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "Got it! May I have your name and mobile number to confirm the booking and send you a reminder?",
        goal: "Capture patient identity",
        successCriteria: ["Name captured == true", "Mobile captured == true"],
        episodicMemory: ["Slot confirmed: Tomorrow 10 AM", "Requesting patient details"],
        workingMemory: { doctor: "Dr. Sharma", slot: "Tomorrow 10:00 AM" },
        confidence: 98,
        sentiment: "Professional / Attentive",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "Sure, it's Priya Nair, and my number is 98400 12345.",
        goal: "Capture patient identity",
        successCriteria: ["Name captured == true", "Mobile captured == true"],
        episodicMemory: ["Patient: Priya Nair", "Mobile: 98400 12345"],
        workingMemory: { patient: "Priya Nair", mobile: "98400 12345", doctor: "Dr. Sharma", slot: "Tomorrow 10:00 AM" },
        confidence: 97,
        sentiment: "Cooperative",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "Wonderful, Priya! Your appointment with Dr. Sharma is confirmed for tomorrow at 10 AM. An SMS reminder will be sent to 98400 12345 one hour before. See you then!",
        goal: "Confirm booking & trigger SMS",
        successCriteria: ["Booking logged in calendar == true", "SMS reminder scheduled == true"],
        episodicMemory: ["Booking confirmed: Priya Nair", "SMS reminder scheduled", "CRM updated"],
        workingMemory: { status: "Booked", reminder: "1 hr before", action: "SMS sent" },
        confidence: 99,
        sentiment: "Warm / Reassuring",
        frustrationSlope: "Negative (-0.4)"
      }
    ]
  },
  {
    name: "Order Verification",
    lang: "Tamil / தமிழ்",
    flag: "🇮🇳",
    title: "E-Commerce COD Verification",
    turns: [
      {
        speaker: "agent",
        text: "வணக்கம், நான் Voise AI-லிருந்து பேசுகிறேன். உங்களது ஆர்டரை உறுதிப்படுத்தலாமா?",
        goal: "Verify order identity",
        successCriteria: ["User confirms identity == true"],
        episodicMemory: ["Initiated COD order verification"],
        workingMemory: { order_id: "VOISE-8842", item: "Poco X6 Pro" },
        confidence: 99,
        sentiment: "Polite / Enthusiastic",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "ஆமாங்க, சொல்லுங்க. என் ஆர்டர் பத்தி தான் கூப்பிடுறீங்களா?",
        goal: "Verify order identity",
        successCriteria: ["User confirms identity == true"],
        episodicMemory: ["User verified identity"],
        workingMemory: { order_id: "VOISE-8842", item: "Poco X6 Pro" },
        confidence: 95,
        sentiment: "Cooperative / Receptive",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "நன்றி! நீங்கள் ஆர்டர் செய்த போகோ எக்ஸ்6 ப்ரோவின் டெலிவரி முகவரி காந்தி நகர், சென்னை. இது சரியா?",
        goal: "Confirm address coordinates",
        successCriteria: ["Address verified == true"],
        episodicMemory: ["User verified identity", "Prompted address check: Gandhi Nagar, Chennai"],
        workingMemory: { order_id: "VOISE-8842", item: "Poco X6 Pro", address: "Gandhi Nagar, Chennai" },
        confidence: 98,
        sentiment: "Helpful",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "user",
        text: "ஆமாங்க, அதுதான் முகவரி. நாளைக்கே டெலிவரி பண்ண முடியுமா?",
        goal: "Confirm address coordinates",
        successCriteria: ["Address verified == true"],
        episodicMemory: ["Address confirmed", "User requested express shipping"],
        workingMemory: { order_id: "VOISE-8842", item: "Poco X6 Pro", address: "Gandhi Nagar, Chennai", request: "Express" },
        confidence: 94,
        sentiment: "Cooperative / Eager",
        frustrationSlope: "Flat (0.0)"
      },
      {
        speaker: "agent",
        text: "கண்டிப்பாக! உங்கள் ஆர்டர் வெற்றிகரமாக உறுதிசெய்யப்பட்டது. நாளை மதியம் 2 மணிக்குள் உங்கள் இல்லத்திற்கு டெலிவரி செய்யப்படும். நன்றி!",
        goal: "Finalize dispatch order",
        successCriteria: ["Dispatch triggered == true"],
        episodicMemory: ["Confirmed express shipping tomorrow", "Logged verified address"],
        workingMemory: { status: "Verified", delivery_time: "Tomorrow 2:00 PM" },
        confidence: 99,
        sentiment: "Polite / Reassuring",
        frustrationSlope: "Negative (-0.3)"
      }
    ]
  }
];

export default function Hero() {
  const [activeScenarioIdx, setActiveScenarioIdx] = useState(0);
  const [currentTurnIdx, setCurrentTurnIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [simulationSpeed, setSimulationSpeed] = useState(3000); // ms per turn
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const scenario = scenarios[activeScenarioIdx];
  const currentTurn = scenario.turns[currentTurnIdx];

  // Auto-play control logic
  useEffect(() => {
    if (isPlaying) {
      timeoutRef.current = setTimeout(() => {
        if (currentTurnIdx < scenario.turns.length - 1) {
          setCurrentTurnIdx((prev) => prev + 1);
        } else {
          setIsPlaying(false);
        }
      }, simulationSpeed);
    }
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [isPlaying, currentTurnIdx, scenario.turns.length, simulationSpeed]);

  const togglePlay = () => {
    if (currentTurnIdx === scenario.turns.length - 1) {
      setCurrentTurnIdx(0);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentTurnIdx(0);
  };

  const handleScenarioChange = (idx: number) => {
    setIsPlaying(false);
    setActiveScenarioIdx(idx);
    setCurrentTurnIdx(0);
  };

  // Generate dynamic wave amplitude based on speaker
  const waveBarsCount = 30;
  const isAgentSpeaking = isPlaying && currentTurn.speaker === "agent";
  const isUserSpeaking = isPlaying && currentTurn.speaker === "user";

  return (
    <section className="relative min-h-screen bg-background text-foreground overflow-hidden pt-28 pb-16 flex items-center">
      {/* Visual background layers */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--primary-foreground,rgba(56,189,248,0.03))_0%,_transparent_60%)] pointer-events-none" />
      <div className="absolute top-[20%] left-[-10%] w-[350px] h-[350px] bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[10%] right-[-10%] w-[450px] h-[450px] bg-accent/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Grid Pattern overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.015)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(0,0,0,0.015)_1px,_transparent_1px)] dark:bg-[linear-gradient(rgba(255,255,255,0.015)_1px,_transparent_1px),_linear-gradient(90deg,_rgba(255,255,255,0.015)_1px,_transparent_1px)] bg-[size:32px_32px] pointer-events-none" />

      <div className="container mx-auto px-4 max-w-7xl relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column: Bold headings & CTAs */}
          <div className="lg:col-span-5 text-left flex flex-col justify-center">
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 text-primary text-xs font-semibold tracking-wider mb-6 w-fit animate-pulse"
            >
              <Sparkles className="size-3 text-accent animate-pulse" />
              <span>Next-Gen Real-Time Voice Technology</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="font-display font-black text-4xl sm:text-5xl xl:text-6xl leading-[1.05] tracking-tight mb-6 uppercase"
            >
              The Call Center <br />
              <span className="text-primary font-black">
                Is Dead.
              </span>{" "}
              <br />
              <span className="text-foreground">AI Agents</span> <br />
              <span className="text-accent font-black">
                Are Here.
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="text-muted-foreground text-base sm:text-lg leading-relaxed mb-8 max-w-lg"
            >
              Deploy real-time autonomous voice agents that speak 12 Indian languages fluently.
               Handle payment reminders, lead qualification, and appointment confirmations 24/7
               with natural conversational flow.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-col sm:flex-row gap-4 mb-8"
            >
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-primary to-cyan-500 text-primary-foreground font-bold text-sm h-12 px-6 rounded-xl hover:brightness-110 active:scale-[0.98] transition-all duration-200 shadow-lg shadow-primary/20"
              >
                Deploy Free Agent
                <ArrowRight className="size-4" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center justify-center gap-2 border border-border text-foreground font-semibold text-sm h-12 px-6 rounded-xl hover:bg-muted/50 transition-colors"
              >
                Explore Technology
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex items-center gap-6 border-t border-border pt-6"
            >
              <div>
                <span className="block text-2xl font-black text-foreground">3×</span>
                <span className="text-xs text-muted-foreground font-medium">Collections ROI</span>
              </div>
              <div className="w-px h-8 bg-border" />
              <div>
                <span className="block text-2xl font-black text-foreground">60%</span>
                <span className="text-xs text-muted-foreground font-medium">Fewer No-Shows</span>
              </div>
              <div className="w-px h-8 bg-border" />
              <div>
                <span className="block text-2xl font-black text-foreground">24/7</span>
                <span className="text-xs text-muted-foreground font-medium">Zero Downtime</span>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Workbench Live Simulation Console */}
          <div className="lg:col-span-7 w-full">
            <motion.div
              initial={{ opacity: 0, scale: 0.98, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
              className="bg-card dark:bg-zinc-950/80 backdrop-blur-xl border border-border dark:border-zinc-800 rounded-3xl overflow-hidden shadow-2xl relative"
            >
              {/* Header Panel */}
              <div className="px-6 py-4 bg-muted/40 dark:bg-zinc-900/50 border-b border-border dark:border-zinc-800/80 flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
                  </div>
                  <div className="h-4 w-px bg-border dark:bg-zinc-800 mx-2" />
                  <span className="text-xs font-semibold text-muted-foreground dark:text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    Live Call Simulation
                  </span>
                </div>

                {/* Scenario tabs */}
                <div className="flex bg-muted dark:bg-zinc-900 border border-border dark:border-zinc-800 rounded-lg p-0.5">
                  {scenarios.map((scen, idx) => (
                    <button
                      type="button"
                      key={idx}
                      onClick={() => handleScenarioChange(idx)}
                      className={`px-3 py-1 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 ${
                        activeScenarioIdx === idx
                          ? "bg-white text-foreground dark:bg-zinc-800 dark:text-foreground shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <span>{scen.flag}</span>
                      <span className="hidden sm:inline">{scen.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Main Sandbox Content Grid */}
              <div className="p-6 grid grid-cols-1 md:grid-cols-12 gap-6">
                
                {/* Left Side: Real-Time Dialogue and SVG Waveform */}
                <div className="md:col-span-7 flex flex-col justify-between min-h-[360px] gap-6">
                  
                  {/* Dynamic Dialogue Panel */}
                  <div className="flex-1 flex flex-col justify-center bg-muted/20 border border-border dark:bg-zinc-900/30 dark:border-zinc-900/90 rounded-2xl p-4 overflow-y-auto min-h-[220px]">
                    <div className="space-y-4">
                      <AnimatePresence mode="popLayout">
                        {scenario.turns.slice(0, currentTurnIdx + 1).map((trn, idx) => {
                          const isLast = idx === currentTurnIdx;
                          return (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, y: 15 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.4 }}
                              className={`flex flex-col ${
                                trn.speaker === "agent" ? "items-start" : "items-end"
                              }`}
                            >
                              <div
                                className={`text-[10px] font-bold uppercase tracking-wider mb-1 flex items-center gap-1.5 ${
                                  trn.speaker === "agent" ? "text-primary" : "text-accent"
                                }`}
                              >
                                {trn.speaker === "agent" ? (
                                  <>
                                    <Sparkles className="size-3" />
                                    VOISE AGENT
                                  </>
                                ) : (
                                  <>
                                    <Smile className="size-3" />
                                    CUSTOMER
                                  </>
                                )}
                              </div>
                              <div
                                className={`px-4 py-2.5 rounded-2xl text-xs md:text-sm leading-relaxed max-w-[85%] font-medium ${
                                  trn.speaker === "agent"
                                    ? "bg-primary/10 text-foreground border border-primary/20 rounded-tl-none"
                                    : "bg-muted text-foreground border border-border dark:bg-zinc-800/80 dark:border-zinc-700/50 rounded-tr-none"
                                }`}
                              >
                                {trn.text}
                              </div>
                              {/* Self-Correction Log Display */}
                              {isLast && trn.correction && (
                                <motion.div
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: "auto" }}
                                  className="mt-1 flex items-center gap-1.5 text-[10px] text-accent font-mono bg-accent/5 px-2 py-0.5 rounded border border-accent/20"
                                >
                                  <Zap className="size-3 animate-pulse" />
                                  <span>Self-Correction: {trn.correction}</span>
                                </motion.div>
                              )}
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>
                  </div>

                  {/* SVG Waveform Audio Visualizer */}
                  <div className="bg-muted/30 dark:bg-zinc-950/60 border border-border dark:bg-zinc-800/50 rounded-2xl p-4 flex flex-col items-center justify-center relative overflow-hidden h-20">
                    <div className="absolute top-2 left-3 text-[10px] text-zinc-500 font-bold uppercase tracking-wider flex items-center gap-1.5">
                      <Volume2 className="size-3 text-primary" />
                      Audio Visualizer
                    </div>
                    <div className="flex items-end gap-[3px] h-10 w-full justify-center">
                      {Array.from({ length: waveBarsCount }).map((_, i) => {
                        // Generate random heights dynamically
                        let heightVal = "4px";
                        if (isAgentSpeaking) {
                          heightVal = `${Math.floor(Math.sin((i + currentTurnIdx) * 0.8) * 20 + 24)}px`;
                        } else if (isUserSpeaking) {
                          heightVal = `${Math.floor(Math.cos(i * 0.5) * 12 + 16)}px`;
                        } else if (isPlaying) {
                          heightVal = "6px"; // Idle/Processing stutter
                        }
                        return (
                          <motion.div
                            key={i}
                            animate={{ height: heightVal }}
                            transition={{
                              type: "spring",
                              stiffness: 300,
                              damping: 15,
                              delay: i * 0.01
                            }}
                            className={`w-[4px] rounded-full ${
                              isAgentSpeaking
                                ? "bg-primary"
                                : isUserSpeaking
                                ? "bg-accent"
                                : "bg-zinc-300 dark:bg-zinc-800"
                            }`}
                          />
                        );
                      })}
                    </div>
                  </div>

                  {/* Simulation Controls */}
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={togglePlay}
                        className={`h-10 px-5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                          isPlaying
                            ? "bg-zinc-200 dark:bg-zinc-800 text-foreground hover:bg-zinc-300 dark:hover:bg-zinc-700"
                            : "bg-primary text-primary-foreground hover:brightness-110 shadow-lg shadow-primary/10"
                        }`}
                      >
                        {isPlaying ? (
                          <>
                            <Pause className="size-3.5 fill-current" />
                            Pause
                          </>
                        ) : (
                          <>
                            <Play className="size-3.5 fill-current" />
                            {currentTurnIdx === scenario.turns.length - 1
                              ? "Restart Simulation"
                              : "Simulate Call"}
                          </>
                        )}
                      </button>
                      <button
                        type="button"
                        onClick={handleReset}
                        className="h-10 w-10 border border-border text-muted-foreground hover:text-foreground rounded-xl flex items-center justify-center transition-colors"
                        title="Reset Call"
                      >
                        <RotateCcw className="size-4" />
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">
                        Speed
                      </span>
                      <select
                        value={simulationSpeed}
                        onChange={(e) => setSimulationSpeed(Number(e.target.value))}
                        className="bg-white dark:bg-zinc-900 border border-border dark:border-zinc-800 rounded-lg text-xs p-1.5 text-foreground font-semibold focus:outline-none"
                      >
                        <option value={4000}>Slower (4s)</option>
                        <option value={3000}>Normal (3s)</option>
                        <option value={2000}>Fast (2s)</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Right Side: AGENTS.md Real-Time Telemetry Panels */}
                <div className="md:col-span-5 flex flex-col gap-4">
                  
                  {/* Goal & Success Criteria Tracker */}
                  <div className="bg-muted/30 border border-border dark:bg-zinc-900/50 dark:border-zinc-850 rounded-2xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] text-primary font-bold uppercase tracking-wider flex items-center gap-1.5">
                          <Target className="size-3.5" />
                          Goal Tracker
                        </span>
                        <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-bold">
                          Active
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-foreground leading-tight mb-2">
                        {currentTurn.goal}
                      </h4>
                      <div className="space-y-1.5">
                        {currentTurn.successCriteria.map((crit, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-[10px]">
                            <CheckCircle className="size-3.5 text-primary shrink-0 mt-0.5" />
                            <span className="font-mono text-zinc-500 dark:text-zinc-400">{crit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {/* Goal Progress Bar */}
                    <div className="mt-4 pt-3 border-t border-border dark:border-zinc-800/80">
                      <div className="flex justify-between text-[9px] text-zinc-500 font-bold mb-1">
                        <span>CALL PROGRESS</span>
                        <span>
                          {Math.round(((currentTurnIdx + 1) / scenario.turns.length) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-zinc-200 dark:bg-zinc-900 rounded-full h-1.5 overflow-hidden">
                        <motion.div
                          animate={{
                            width: `${((currentTurnIdx + 1) / scenario.turns.length) * 100}%`
                          }}
                          className="h-full bg-gradient-to-r from-primary to-cyan-400"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Multi-Layer Memory Governance */}
                  <div className="bg-muted/30 border border-border dark:bg-zinc-900/50 dark:border-zinc-850 rounded-2xl p-4">
                    <div className="flex items-center gap-1.5 mb-3">
                      <Brain className="size-3.5 text-accent" />
                      <span className="text-[10px] text-accent font-bold uppercase tracking-wider">
                        Multi-Layer Memory
                      </span>
                    </div>

                    <div className="space-y-2.5">
                      {/* Episodic memory */}
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1">
                          Episodic Memory (Current Call)
                        </div>
                        <ul className="space-y-1">
                          {currentTurn.episodicMemory.slice(-2).map((item, idx) => (
                            <li key={idx} className="text-[10px] text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                              <ChevronRight className="size-3 text-zinc-400 dark:text-zinc-500 shrink-0" />
                              <span className="truncate">{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Working memory (Key-Value) */}
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1">
                          Working Memory (Structured)
                        </div>
                        <div className="grid grid-cols-2 gap-1.5">
                          {Object.entries(currentTurn.workingMemory).map(([k, v]) => (
                            <div
                              key={k}
                              className="bg-white dark:bg-zinc-950/60 rounded px-2 py-1 text-[9px] border border-border dark:border-zinc-800/80 font-mono truncate"
                            >
                              <span className="text-zinc-500">{k}: </span>
                              <span className="text-zinc-700 dark:text-zinc-300">{v}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Trust metrics: Confidence, Emotion, Turn */}
                  <div className="bg-muted/30 border border-border dark:bg-zinc-900/50 dark:border-zinc-850 rounded-2xl p-4 grid grid-cols-2 gap-4">
                    
                    {/* Confidence Tracker */}
                    <div className="flex flex-col justify-between">
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1.5">
                          Confidence
                        </div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-2xl font-black text-foreground">
                            {currentTurn.confidence}%
                          </span>
                        </div>
                      </div>
                      <div className="text-[9px] text-zinc-600 dark:text-zinc-400 font-semibold bg-white dark:bg-zinc-950/40 border border-border dark:border-zinc-800/50 px-1.5 py-0.5 rounded w-fit">
                        STT / Intent Match
                      </div>
                    </div>

                    {/* Emotional & Conversational Tracker */}
                    <div className="flex flex-col justify-between">
                      <div>
                        <div className="text-[9px] text-zinc-500 font-bold uppercase mb-1">
                          Sentiment Trend
                        </div>
                        <div className="text-[10px] font-bold text-foreground truncate">
                          {currentTurn.sentiment}
                        </div>
                      </div>
                      <div className="text-[9px] text-zinc-500">
                        Slope:{" "}
                        <span className="text-foreground font-mono font-bold">
                          {currentTurn.frustrationSlope}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Interruption & Turn Ownership indicator */}
                  <div className="bg-muted/30 border border-border dark:bg-zinc-900/50 dark:border-zinc-850 rounded-2xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Activity className="size-3.5 text-zinc-400" />
                      <span className="text-[9px] text-zinc-500 font-bold uppercase">
                        Turn Ownership
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <span
                        className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all ${
                          isPlaying && currentTurn.speaker === "agent"
                            ? "bg-primary/20 text-primary border-primary/30"
                            : "bg-white text-zinc-400 border-border dark:bg-zinc-900 dark:text-zinc-600 dark:border-zinc-800"
                        }`}
                      >
                        Speaking
                      </span>
                      <span
                        className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border transition-all ${
                          isPlaying && currentTurn.speaker === "user"
                            ? "bg-accent/20 text-accent border-accent/30"
                            : "bg-white text-zinc-400 border-border dark:bg-zinc-900 dark:text-zinc-600 dark:border-zinc-800"
                        }`}
                      >
                        Barge-in Allowed
                      </span>
                    </div>
                  </div>

                </div>
              </div>
            </motion.div>
          </div>

        </div>
      </div>
    </section>
  );
}
