import { createContext, useContext, useState, useEffect } from 'react';
import { auth, signInWithGoogle, logOut } from './firebase';
import axios from 'axios';

const AuthContext = createContext();

// Add your premium emails here to unlock unlimited generation
export const PREMIUM_USERS_LIST = [
  'hamzaraeescarpet@gmail.com' 
];

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [credits, setCredits] = useState(5);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(user => {
      setCurrentUser(user);
      if (user) {
        // Register user email in database for marketing analytics
        axios.post('/api/hf/register-user', { email: user.email })
          .catch(err => console.error("Error registering user", err));

        if (PREMIUM_USERS_LIST.includes(user.email)) {
          setIsPremium(true);
          const todayStr = new Date().toLocaleDateString('en-US'); // e.g. "5/28/2026"
          const savedDate = localStorage.getItem(`quota_date_${user.uid}`);
          
          if (savedDate !== todayStr) {
            // Day changed! Reset daily premium credits to 100
            localStorage.setItem(`quota_date_${user.uid}`, todayStr);
            localStorage.setItem(`credits_${user.uid}`, 100);
            setCredits(100);
          } else {
            const savedCredits = localStorage.getItem(`credits_${user.uid}`);
            setCredits(savedCredits !== null ? parseInt(savedCredits) : 100);
          }
        } else {
          setIsPremium(false);
          const todayStr = new Date().toLocaleDateString('en-US'); // e.g. "5/28/2026"
          const savedDate = localStorage.getItem(`quota_date_${user.uid}`);
          
          if (savedDate !== todayStr) {
            // Day changed! Reset daily free credits to 5
            localStorage.setItem(`quota_date_${user.uid}`, todayStr);
            localStorage.setItem(`credits_${user.uid}`, 5);
            setCredits(5);
          } else {
            const savedCredits = localStorage.getItem(`credits_${user.uid}`);
            setCredits(savedCredits !== null ? parseInt(savedCredits) : 5);
          }
        }
      } else {
        setIsPremium(false);
        setCredits(5);
      }
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  const consumeCredits = (amount) => {
    if (credits >= amount) {
      const newCredits = credits - amount;
      setCredits(newCredits);
      localStorage.setItem(`credits_${currentUser.uid}`, newCredits);
      return true;
    }
    return false;
  };

  const value = {
    currentUser,
    isPremium,
    credits,
    consumeCredits,
    login: signInWithGoogle,
    logout: logOut
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
