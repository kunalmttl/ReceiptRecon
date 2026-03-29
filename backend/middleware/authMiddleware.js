const supabase = require('../config/supabase');

/**
 * Super simple middleware to simulate an authenticated user for testing.
 * Refactored to use Supabase (profiles table) instead of Mongoose (models/userModel).
 */
const protect = async (req, res, next) => {
  let userId;
  
  // We'll pass the user ID in a custom header (e.g., from Postman or Frontend)
  if (req.headers['x-user-id'] || req.headers['authorization']) {
    try {
      userId = req.headers['x-user-id'] || req.headers['authorization'];

      // Note: In a real Supabase Auth setup, we'd use supabase.auth.getUser(token)
      // For this project stage, we're using the UUID provided in the request.
      
      const { data: user, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      if (error || !user) {
        return res.status(401).json({ message: 'Not authorized, user not found' });
      }

      // Attach the user object and proceed
      req.user = user;
      next();

    } catch (error) {
      console.error('Auth Middleware Error:', error.message);
      res.status(401).json({ message: 'Not authorized, token/ID failed' });
    }
  } else {
    res.status(401).json({ message: 'Not authorized, no user ID provided' });
  }
};

module.exports = { protect };