module.exports = function(eleventyConfig) {
  // Copy static assets
  eleventyConfig.addPassthroughCopy("static");
  eleventyConfig.addPassthroughCopy("favicon.ico");
  
  return {
    dir: {
      input: ".",
      output: "_site"
    }
  };
};