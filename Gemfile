source "https://rubygems.org"

# modern jekyll, built + deployed via github actions (see .github/workflows/pages.yml).
# the legacy github-pages gem is intentionally NOT used: it pins jekyll 3.9 / liquid 4.0,
# which call Object#tainted? and break on ruby 3.2+ (this machine runs ruby 4.0).
gem "jekyll", "~> 4.4"

# default gems unbundled by modern ruby; declared explicitly so bundler resolves them.
gem "csv"
gem "bigdecimal"
gem "webrick"       # needed by `jekyll serve` since ruby 3.0

group :jekyll_plugins do
  gem "jekyll-feed", "~> 0.17"
  gem "jekyll-sitemap", "~> 1.4"
end

# windows / jruby lack zoneinfo; bundle tzinfo data there.
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# faster directory watching on windows.
gem "wdm", "~> 0.1.1", :platforms => [:mingw, :x64_mingw, :mswin]
