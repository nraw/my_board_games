const fs = require('fs');
const path = require('path');

module.exports = function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("static");

  eleventyConfig.addCollection("users", function(collectionApi) {
    const filePath = path.join(__dirname, "_data", "suggested_players.json");
    const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    return Object.keys(data);
  });
};
