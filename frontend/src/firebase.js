import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyCK9djJc67GfseUo_k6xL6YrfA4SFBgMzo",
  authDomain: "quizviral-ai.firebaseapp.com",
  projectId: "quizviral-ai",
  storageBucket: "quizviral-ai.firebasestorage.app",
  messagingSenderId: "845054526911",
  appId: "1:845054526911:web:cda948993c5badd2ffcd0a",
  measurementId: "G-NETYNRRK90"
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();

export const signInWithGoogle = () => signInWithPopup(auth, provider);
export const logOut = () => signOut(auth);
