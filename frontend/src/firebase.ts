import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "AIzaSyBe-36YrX4D8fx5hM73vM_UGGzahWlrsxc",
  authDomain: "worship-flow-479220.firebaseapp.com",
  projectId: "worship-flow-479220",
  storageBucket: "worship-flow-479220.firebasestorage.app",
  messagingSenderId: "1058569893266",
  appId: "1:1058569893266:web:fcb0f623338a49b47abd4b"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
