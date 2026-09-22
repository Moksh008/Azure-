import { initializeApp } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  GithubAuthProvider,
} from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAlXPVq-Ufa5q1reCQL5dndoqjCveGHLOg",
  authDomain: "beesem5.firebaseapp.com",
  projectId: "beesem5",
  storageBucket: "beesem5.firebasestorage.app",
  messagingSenderId: "879793894497",
  appId: "1:879793894497:web:0eaa528511c2664795e620",
  measurementId: "G-GH0HMM5XN2",
};

export const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();
