import {
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  deleteDoc,
  query,
  orderBy,
  serverTimestamp,
  Timestamp,
} from "firebase/firestore";
import { db } from "./firebase";
import type {
  OpenAlexPaper,
  GroundedAnswer,
  PaperAnalysis,
  PaperComparison,
  ResearchOpportunity,
  ProjectProposal,
  FeasibilityAssessment,
  PRDDocument,
} from "../types";

export type Turn =
  | { kind: "text"; role: "user" | "assistant"; content: string }
  | { kind: "papers"; papers: OpenAlexPaper[] }
  | {
      kind: "answer";
      question: string;
      answer: GroundedAnswer;
    }
  | { kind: "analyses"; analyses: PaperAnalysis[] }
  | { kind: "comparison"; comparison: PaperComparison }
  | { kind: "opportunities"; opportunities: ResearchOpportunity[] }
  | { kind: "proposals"; proposals: ProjectProposal[] }
  | {
      kind: "feasibility";
      proposal: ProjectProposal;
      assessment: FeasibilityAssessment;
    }
  | { kind: "prd"; prd: PRDDocument; proposal?: ProjectProposal };

export interface ChatSessionMeta {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  paperIds: string[];
  messageCount: number;
}

export interface ChatSession extends ChatSessionMeta {
  turns: Turn[];
}

export function generateChatTitle(firstQuery: string): string {
  const clean = firstQuery
    .replace(/^\[(Search|Think|Canvas):\s*/i, "")
    .replace(/\]$/, "")
    .trim();
  if (!clean) return "Research Session";
  return clean.length > 38 ? clean.substring(0, 38) + "..." : clean;
}

export async function saveChatSession(
  userId: string,
  chatId: string,
  turns: Turn[],
  title?: string,
  paperIds: string[] = []
): Promise<void> {
  if (!userId || !chatId) return;

  const chatRef = doc(db, "users", userId, "chats", chatId);
  const existingSnap = await getDoc(chatRef);

  let sessionTitle = title;
  if (!sessionTitle) {
    if (existingSnap.exists() && existingSnap.data()?.title) {
      sessionTitle = existingSnap.data().title;
    } else {
      const firstUserMsg = turns.find(
        (t) => t.kind === "text" && t.role === "user"
      );
      sessionTitle = firstUserMsg && firstUserMsg.kind === "text"
        ? generateChatTitle(firstUserMsg.content)
        : "Research Investigation";
    }
  }

  // Convert complex Turn items to plain JSON
  const serializedTurns = JSON.parse(JSON.stringify(turns));

  await setDoc(
    chatRef,
    {
      title: sessionTitle,
      turns: serializedTurns,
      paperIds: paperIds || [],
      messageCount: turns.length,
      updatedAt: serverTimestamp(),
      ...(!existingSnap.exists() ? { createdAt: serverTimestamp() } : {}),
    },
    { merge: true }
  );
}

export async function loadUserChatSessions(
  userId: string
): Promise<ChatSessionMeta[]> {
  if (!userId) return [];

  const chatsRef = collection(db, "users", userId, "chats");
  const q = query(chatsRef, orderBy("updatedAt", "desc"));
  const snapshot = await getDocs(q);

  return snapshot.docs.map((docSnap) => {
    const data = docSnap.data();
    const createdAt = data.createdAt instanceof Timestamp
      ? data.createdAt.toDate()
      : new Date();
    const updatedAt = data.updatedAt instanceof Timestamp
      ? data.updatedAt.toDate()
      : new Date();

    return {
      id: docSnap.id,
      title: data.title || "Research Conversation",
      createdAt,
      updatedAt,
      paperIds: data.paperIds || [],
      messageCount: data.turns?.length || data.messageCount || 0,
    };
  });
}

export async function loadChatSession(
  userId: string,
  chatId: string
): Promise<ChatSession | null> {
  if (!userId || !chatId) return null;

  const chatRef = doc(db, "users", userId, "chats", chatId);
  const snap = await getDoc(chatRef);

  if (!snap.exists()) return null;

  const data = snap.data();
  const createdAt = data.createdAt instanceof Timestamp
    ? data.createdAt.toDate()
    : new Date();
  const updatedAt = data.updatedAt instanceof Timestamp
    ? data.updatedAt.toDate()
    : new Date();

  return {
    id: snap.id,
    title: data.title || "Research Conversation",
    createdAt,
    updatedAt,
    paperIds: data.paperIds || [],
    messageCount: data.turns?.length || 0,
    turns: (data.turns as Turn[]) || [],
  };
}

export async function deleteChatSession(
  userId: string,
  chatId: string
): Promise<void> {
  if (!userId || !chatId) return;
  const chatRef = doc(db, "users", userId, "chats", chatId);
  await deleteDoc(chatRef);
}
