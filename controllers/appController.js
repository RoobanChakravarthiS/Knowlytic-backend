const bcrypt = require("bcrypt");
const { ObjectId } = require("mongodb"); // Make sure to import ObjectId
const { connectToDatabase } = require("../utils/db"); // Import your database connection function
const timeStampGenerator = () => new Date();
const multer = require("multer");
const path = require("path");
const { spawn } = require('child_process');
const fs = require('fs');
// const { default: GenericTouchable } = require("react-native-gesture-handler/lib/typescript/components/touchables/GenericTouchable");

async function signup(req, res) {
  const client = await connectToDatabase();
  const { number, password, schoolCode, name } = req.body;
  const collection = client.db("Appdata").collection("users"); // Replace with your actual database name
  const user = await collection.findOne({ phone: number }); 

  if (user) {
    res.status(400).json({ message: "User already exists" });
  } else { 
    const userId = new ObjectId(); // Generate a new ObjectId for user
    const hashedPassword = await bcrypt.hash(password.toString(), 10);
    const profileImage = req.file ? req.file.buffer.toString("base64") : null; // Get the base64 image if exists

    const userData = {
      _id: userId, // Set the user ID as the ObjectId
      email: "",
      phone: number,
      password: hashedPassword,
      schoolCode: schoolCode,
      role: "user", // Default role can be 'user' or you can customize it
      name: name, // Initially empty, can be updated later
      profileImage: profileImage,
      courses: [], // Initialize as an empty array
      points: 0, // Initialize points
      posts: [], // Initialize posts as an empty array
    };

    try {
      await collection.insertOne(userData); // Insert the new user into the collection
      res
        .status(201)
        .json({ message: "User created successfully", userId: userId });
    } catch (error) {
      res
        .status(500)
        .json({ message: "Error creating user", error: error.message });
    } finally {
      client.close(); // Close the database connection
      console.log("Disconnected from the database");
    }
  }
}

async function likepost(req, res) {
  console.log("Received a like request");

  const client = await connectToDatabase();
  const postId = req.params.id;
  const userId = req.body.userId; // Pass the userId to track who liked
  const collection = client.db("Appdata").collection("posts");
  const userCollection = client.db('Appdata').collection('users');
  
  console.log("Post ID:", postId);
  console.log("User ID:", userId);

  // Ensure postId is valid
  if (!ObjectId.isValid(postId)) {
    return res.status(400).json({ message: "Invalid Post ID" });
  }

  try {
    // Find the post by its postId
    const post = await collection.findOne({ _id: new ObjectId(postId) });

    if (!post) {
      return res.status(404).json({ message: "Post not found" });
    }

    const postedUserId = post.userId; // Assuming you store userId in each post
    console.log("Posted User ID:", postedUserId);

    // Check if the user has already liked the post
    const hasLiked = post.likes.includes(userId);

    // Toggle like/unlike based on the current state
    let updatedLikes;
    if (hasLiked) {
      updatedLikes = post.likes.filter((id) => id !== userId); // Remove like
    } else {
      updatedLikes = [...post.likes, userId]; // Add like
    }

    // Update the likes in the post collection
    await collection.updateOne(
      { _id: new ObjectId(postId) }, // Use postId for the update
      { $set: { likes: updatedLikes } }
    );

    // Update the likes inside the user's posts array
    await userCollection.updateOne(
      { _id: new ObjectId(postedUserId), "posts._id": new ObjectId(postId) }, // Find the user and the post in the array
      { $set: { "posts.$.likes": updatedLikes } }  // Use the positional operator to update the likes of the post
    );

    res.status(200).json({
      message: "Post likes updated successfully",
      likes: updatedLikes,
    });
  } catch (error) {
    console.error("Error updating likes:", error); // Log the error for debugging
    res.status(500).json({ message: "Error updating likes", error });
  }
}

async function postComments(req, res) {
  const postId  = req.params.postId;
  const { userId, comment } = req.body;
  console.log(comment)
  console.log(userId)
  const client = await connectToDatabase();
  const collection = client.db("Appdata").collection("posts");
  const userCollection = client.db("Appdata").collection("users");  
  if (!comment || !userId) {
    return res
      .status(400)
      .json({ message: "User ID and comment are required." });
  }

  try {
    const post = await collection.findOne({ _id: new ObjectId(postId) });
    const postedUserId = post.userId;
    if (!post) {
      return res.status(404).json({ message: "Post not found." });
    }

    const newComment = {
      userId,
      comment,
      date: new Date(),
    };

    const updatedPost = await collection.updateOne(
      { _id: new ObjectId(postId) },
      { $push: { comments: newComment } }
    );

    const userUpdatedPost = await userCollection.updateOne(
      {_id : new ObjectId(postedUserId)},
      {$push: {posts: {_id: new ObjectId(postId), comments: [newComment]}}}
    )

    if (updatedPost.modifiedCount === 1 && userUpdatedPost.modifiedCount===1) {
      res.status(200).json({
        message: "Comment added successfully",
        comments: [...post.comments, newComment],
      });
    } else {
      res.status(500).json({ message: "Failed to add comment" });
    }
  } catch (error) {
    res.status(500).json({ message: "Internal Server Error", error });
  }
}
async function getComments(req, res) {
  const { postId } = req.params;
  const client = await connectToDatabase();
  const collection = client.db("Appdata").collection("posts");
  try {
    const post = await collection.findOne({ _id: new ObjectId(postId) });

    if (!post) {
      return res.status(404).json({ message: "Post not found." });
    }

    res.status(200).json(post.comments);
  } catch (error) {
    res.status(500).json({ message: "Internal Server Error", error });
  }
}
async function updateDetails(req, res) {
  console.log("Received request to update user details");
  console.log("User ID from params:", req.params.id);

  const client = await connectToDatabase();
  const userId = req.params.id;

  // Check if req.file is available
  console.log("Uploaded file:", req.file);

  const { name, schoolCode, email, phone } = req.body;
  console.log(name);
  // Validate ObjectId
  if (!ObjectId.isValid(userId)) {
    console.log(`Invalid User ID Format: ${userId}`);
    return res.status(400).json({ message: "Invalid user ID format" });
  }

  // Get profileImage if available
  const profileImage = req.file ? req.file.path : null;

  // Prepare the fields to update
  const updatedFields = { name, schoolCode, email, phone };
  if (profileImage) {
    updatedFields.profileImage = profileImage; // Add the profile image path if available
  }

  // Log the updated fields
  console.log("Updated fields:", updatedFields);

  try {
    const collection = client.db("Appdata").collection("users");

    const updatedUser = await collection.findOneAndUpdate(
      { _id: new ObjectId(userId) },
      { $set: updatedFields },
      { returnOriginal: false }
    );

    if (!updatedUser) {
      return res.status(404).json({ message: "User not found" });
    }

    res.status(200).json(updatedUser);
  } catch (error) {
    console.error("Error updating user details", error);
    res.status(500).json({
      message: "Error updating user details",
      error: error.message || error,
    });
  }
}

async function postAchievement(req, res) {
  const client = await connectToDatabase();
  const { title, description, date, category } = req.body;
  const userId = req.params.id;

  // Check if the files exist
  const imageUri =
    req.files && req.files["image"] ? req.files["image"][0].path : null;
  const pdfUri =
    req.files && req.files["pdf"] ? req.files["pdf"][0].path : null;

  console.log(imageUri);
  console.log(pdfUri);

  try {
    const collection = client.db("Appdata").collection("posts");
    const userCollection = client.db("Appdata").collection("users");
    const notificationCollection = client.db("Appdata").collection("notifications");

    // Find the user to get their name and profile image
    const user = await userCollection.findOne({ _id: new ObjectId(userId) });
    
    if (!user) {
      return res.status(404).json({ error: "User not found." });
    }

    const username = user.name;
    const profile = user.profileImage;
    console.log(profile + " hi here")

    // Create the new post object
    const newPost = {
      title,
      description,
      date: new Date(date),
      category,
      imageUri,
      pdfUri,
      points: 10,
      likes: [],
      comments: [],
      userId,
      name: username,
      profile: profile,
    };

    const result = await collection.insertOne(newPost);

    const postToInsert = {
      ...newPost,
      _id: result.insertedId,
    };

    // Update the user's posts array and increment points
    const updateResult = await userCollection.findOneAndUpdate(
      { _id: new ObjectId(userId) },
      { $push: { posts: postToInsert }, $inc: { points: 10 } },
      { returnDocument: "after" } // Return the updated document
    );

    if (!updateResult) {
      return res.status(404).json({ error: "User not found or update failed." });
    }

    // Create a notification
    const notificationMessage = `${username} has posted a new achievement! Check it out!`;
    const notification = {
      userId: new ObjectId(userId), // Assuming you want to notify the same user
      message: notificationMessage,
      read: false, // New notifications are unread
      createdAt: new Date(),
      name: username,
    };

    await notificationCollection.insertOne(notification);

    res.status(201).json({
      message: "Achievement posted and notification sent!",
      post: postToInsert,
    });
  } catch (error) {
    console.error("Error posting achievement:", error);
    res.status(500).json({ error: "Internal Server Error" });
  } finally {
    client.close();
    console.log("disconnected"); 
  }
}



async function generateReport(req, res) {
    const { author_name } = req.body;

    // Check if author_name is provided
    if (!author_name) {
        return res.status(400).json({ error: 'author_name is required' });
    }

    const reportsFolderPath = path.join(__dirname, 'reports');

    // Create the reports folder if it doesn't exist
    if (!fs.existsSync(reportsFolderPath)) {
        fs.mkdirSync(reportsFolderPath, { recursive: true });
    }

    const pythonScriptPath = path.join(__dirname, 'generate_report.py');

    // Spawn the Python process
    const pythonProcess = spawn('python', [pythonScriptPath, author_name]);

    pythonProcess.on('error', (error) => {
        console.error('Failed to start subprocess:', error);
        return res.status(500).json({ error: 'Failed to start report generation.' });
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', async (code) => {
        console.log(`Python script exited with code ${code}`);
        if (code === 0) {
            const filePath = path.join(reportsFolderPath, `${author_name}_report.pdf`);

            // Check if the file exists 
            try {
                await fs.promises.access(filePath);
                // Send the PDF file to the client
                res.download(filePath, `${author_name}_report.pdf`, (downloadErr) => {
                    if (downloadErr) {
                        console.error('Error sending file:', downloadErr);
                        return res.status(500).send('Error sending file.');
                    }
                    // Delete the report file after sending
                    fs.unlink(filePath, (unlinkErr) => {
                        if (unlinkErr) {
                            console.error('Error deleting file:', unlinkErr);
                        }
                    });
                });
            } catch (err) {
                console.error('Error checking file existence:', err);
                return res.status(500).json({ error: 'Report file not found.' });
            }
        } else {
            console.error(`Python script failed with exit code ${code}`);
            res.status(500).json({ error: 'Failed to generate report.' });
        }
    });
}

async function getNotifications(req, res) {
  const client = await connectToDatabase(); // Make sure to await the connection
  try {
    const collection = client.db('Appdata').collection('notifications');
    const notifications = await collection.find({}).toArray();

    if (notifications.length > 0) { // Check if the notifications array has items
      res.status(200).json(notifications);
    } else {
      res.status(404).json({ message: "No notifications found" });
    }
  } catch (error) {
    console.error("Error fetching notifications:", error); // Log error for debugging
    res.status(500).json({ message: "Internal Server Error" }); // Return an appropriate error response
  } finally {
    await client.close(); // Make sure to await the close method
    console.log('Disconnected from database');
  }
}


async function getPosts(req, res) {
  const client = await connectToDatabase();

  try {
    const postsCollection = client.db("Appdata").collection("posts"); // Replace with your actual database name
    const allPosts = await postsCollection.find({}).toArray(); // Fetch all posts

    if (!allPosts || allPosts.length === 0) {
      return res.status(404).json({ message: "No posts found" });
    }

    res.status(200).json(allPosts); // Send all posts in the response
  } catch (error) {
    res
      .status(500)
      .json({ message: "Error fetching posts", error: error.message });
  } finally {
    client.close();
    console.log("Disconnected from the database");
  }
}

async function getUser(req, res) {
  const client = await connectToDatabase();
  const userId = req.params.id;

  try {
    const collection = client.db("Appdata").collection("users"); // Replace with your actual database name
    const user = await collection.findOne({ _id: new ObjectId(userId) });

    if (!user) {
      return res.status(404).json({ message: "User not found" });
    }

    // Exclude sensitive data like password before sending user data
    const { password, ...userDetails } = user;

    res.status(200).json(userDetails);
  } catch (error) {
    res
      .status(500)
      .json({ message: "Error fetching user details", error: error.message });
  } finally {
    client.close();
    console.log("Disconnected from the database");
  }
}
async function login(req, res) {
  const client = await connectToDatabase();
  const { number, password } = req.body; // Expecting mobile number and password from request body
  const collection = client.db("Appdata").collection("users"); // Replace with your actual database name

  try {
    // Find the user by mobile number
    const user = await collection.findOne({ phone: number });

    if (!user) {
      return res.status(400).json({ message: "User not found" });
    }

    // Compare the provided password with the stored hashed password
    const isPasswordValid = await bcrypt.compare(
      password.toString(),
      user.password
    );

    if (!isPasswordValid) {
      return res.status(400).json({ message: "Invalid password" });
    }

    // Successful login
    res.status(200).json({ message: "Login successful", userId: user._id });
  } catch (error) {
    res.status(500).json({ message: "Error logging in", error: error.message });
  } finally {
    client.close(); // Close the database connection
    console.log("Disconnected from the database");
  }
}
// async function createAchievement(req, res) {
//     const client = await connectToDatabase();
//     const { userId, title, description, date, category } = req.body;

//     // Extract uploaded files from req.files
//     const attachments = req.files.attachments.map(file => ({
//         type: file.mimetype.startsWith('image') ? 'image' : 'file',
//         url: file.path, // This should point to the file location
//         fileName: file.filename,
//         mimeType: file.mimetype,
//     }));

//     try {
//         const collection = client.db('Appdata').collection('achievements'); // Replace with your actual database name

//         // Create the new achievement object
//         const newAchievement = {
//             userId: userId, // Set the user ID
//             title: title,
//             description: description,
//             date: new Date(date), // Ensure date is in Date format
//             category: category,
//             attachments: attachments,
//         };

//         // Save the achievement to the database
//         const achievementResult = await collection.insertOne(newAchievement);

//         // Update the user's posts in the users collection
//         const usersCollection = client.db('Appdata').collection('users'); // Replace with your actual database name
//         await usersCollection.updateOne(
//             { _id: userId },
//             {
//                 $push: {
//                     posts: {
//                         postId: achievementResult.insertedId, // Use the ID of the new achievement
//                         title,
//                         description,
//                         date,
//                         category,
//                         attachments,
//                     },
//                 },
//             }
//         );

//         res.status(201).json({
//             achievement: newAchievement,
//             message: "Achievement created successfully",
//         });
//     } catch (error) {
//         res.status(500).json({ message: "Error creating achievement", error: error.message });
//     } finally {
//         client.close(); // Close the database connection
//         console.log("Disconnected from the database");
//     }
// }

module.exports = {
  login,
  signup,
  getUser,
  updateDetails,
  postAchievement,
  getPosts,
  likepost,
  postComments,
  getComments,
  getNotifications,
  generateReport,
};
