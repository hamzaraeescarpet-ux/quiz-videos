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

        // Fetch premium status from database dynamically
        axios.get(`/api/hf/check-premium?email=${encodeURIComponent(user.email)}`)
          .then(res => {
            const hasPremium = res.data.is_premium || PREMIUM_USERS_LIST.includes(user.email);
            setIsPremium(hasPremium);
            
            const todayStr = new Date().toLocaleDateString('en-US');
            const savedDate = localStorage.getItem(`quota_date_${user.uid}`);
            const defaultCredits = hasPremium ? 100 : 5;

            if (savedDate !== todayStr) {
              localStorage.setItem(`quota_date_${user.uid}`, todayStr);
              localStorage.setItem(`credits_${user.uid}`, defaultCredits);
              setCredits(defaultCredits);
            } else {
              const savedCredits = localStorage.getItem(`credits_${user.uid}`);
              setCredits(savedCredits !== null ? parseInt(savedCredits) : defaultCredits);
            }
          })
          .catch(err => {
            console.error("Error checking premium status", err);
            // Fallback to offline check
            const hasPremium = PREMIUM_USERS_LIST.includes(user.email);
            setIsPremium(hasPremium);
            const defaultCredits = hasPremium ? 100 : 5;
            const todayStr = new Date().toLocaleDateString('en-US');
            const savedDate = localStorage.getItem(`quota_date_${user.uid}`);
            if (savedDate !== todayStr) {
              localStorage.setItem(`quota_date_${user.uid}`, todayStr);
              localStorage.setItem(`credits_${user.uid}`, defaultCredits);
              setCredits(defaultCredits);
            } else {
              const savedCredits = localStorage.getItem(`credits_${user.uid}`);
              setCredits(savedCredits !== null ? parseInt(savedCredits) : defaultCredits);
            }
          });
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
      if (currentUser) {
        localStorage.setItem(`credits_${currentUser.uid}`, newCredits);
      }
      return true;
    }
    return false;
  };

  const refreshUserStatus = async () => {
    if (!auth.currentUser) return false;
    const user = auth.currentUser;
    try {
      const res = await axios.get(`/api/hf/check-premium?email=${encodeURIComponent(user.email)}`);
      const hasPremium = res.data.is_premium || PREMIUM_USERS_LIST.includes(user.email);
      setIsPremium(hasPremium);
      
      const todayStr = new Date().toLocaleDateString('en-US');
      const defaultCredits = hasPremium ? 100 : 5;
      
      localStorage.setItem(`quota_date_${user.uid}`, todayStr);
      localStorage.setItem(`credits_${user.uid}`, defaultCredits);
      setCredits(defaultCredits);
      return hasPremium;
    } catch (err) {
      console.error("Error refreshing premium status", err);
      return false;
    }
  };

  const value = {
    currentUser,
    isPremium,
    credits,
    consumeCredits,
    refreshUserStatus,
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
