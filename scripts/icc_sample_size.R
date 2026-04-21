# ICC Reliability Study - Required Sample Size Calculation
# Package: ICC.Sample.Size
# Parameters: p = 0.75, p0 = 0, k = 2 raters, alpha = 0.05, power = 0.95, two-tailed

if (!requireNamespace("ICC.Sample.Size", quietly = TRUE)) {
  install.packages("ICC.Sample.Size")
}
library(ICC.Sample.Size)

result <- calculateIccSampleSize(p = 0.75, p0 = 0, k = 2, alpha = 0.05, power = 0.95)
print(result)


#Ran in cmd with full file paths because R wasnt on my path
#"C:\Program Files\R\R-4.5.3\bin\Rscript.exe" "C:\EEG_Dissertation\scripts\icc_sample_size.R"

# Result:
#    N    p p0 k alpha tails power
# 1 15 0.75  0 2  0.05     2  0.95
# Required sample size: N = 15 participants
