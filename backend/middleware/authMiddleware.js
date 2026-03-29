const supabase = require('../config/db');

// Super simple middleware to simulate an authenticated user for testing
const protect = async (req, res, next) => 
{
  let userId;
  // We'll pass the user ID in a custom header for Postman tests
  if (req.headers['x-user-id']) {
    try {
      userId = req.headers['x-user-id'];

      // Find the user profile in Supabase
      const { data: user, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .single();

      // If no user is found with that ID, stop right here.
      if (error || !user) {
        return res.status(401).json({ message: 'Not authorized, user not found' });
      }

      // If we get here, the user is valid. Attach it and proceed.
      req.user = user;
      next();

    } catch (error) {
      console.error(error);
      res.status(401).json({ message: 'Not authorized, token/ID failed' });
    }
  } else {
    res.status(401).json({ message: 'Not authorized, no user ID provided' });
  }
};



module.exports = { protect };