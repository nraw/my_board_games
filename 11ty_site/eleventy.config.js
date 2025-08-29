module.exports = function(eleventyConfig) {
  // Copy static assets
  eleventyConfig.addPassthroughCopy("static");
  
  return {
    dir: {
      input: ".",
      output: "_site"
    }
  };
};