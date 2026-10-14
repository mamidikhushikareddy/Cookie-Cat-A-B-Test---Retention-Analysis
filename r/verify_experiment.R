#!/usr/bin/env Rscript
# Independent verification in base R. Does NOT call the Python engine.
# Usage: Rscript r/verify_experiment.R data/raw/cookie_cats.csv [alloc_gate30=0.5]
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !file.exists(args[1])) { message("ERROR: CSV path missing or not found"); quit(status = 2) }
alloc30 <- if (length(args) >= 2) as.numeric(args[2]) else 0.5
d <- read.csv(args[1], stringsAsFactors = FALSE)
need <- c("userid", "version", "sum_gamerounds", "retention_1", "retention_7")
if (!all(need %in% names(d))) { message("ERROR: missing columns"); quit(status = 2) }
asl <- function(x) tolower(as.character(x)) %in% c("true", "1")
d$r1 <- asl(d$retention_1); d$r7 <- asl(d$retention_7)
cat(sprintf("rows=%d unique_ids=%d dup_ids=%d missing_cells=%d\n", nrow(d), length(unique(d$userid)),
            sum(duplicated(d$userid)), sum(is.na(d[need]))))
g30 <- d[d$version == "gate_30", ]; g40 <- d[d$version == "gate_40", ]
n30 <- nrow(g30); n40 <- nrow(g40)
cmp <- function(col) {
  x30 <- sum(g30[[col]]); x40 <- sum(g40[[col]]); p30 <- x30/n30; p40 <- x40/n40
  se_w <- sqrt(p30*(1-p30)/n30 + p40*(1-p40)/n40); z <- qnorm(0.975)
  pp <- (x30 + x40)/(n30 + n40); zt <- (p40 - p30)/sqrt(pp*(1-pp)*(1/n30 + 1/n40))
  cat(sprintf("%s: n30=%d x30=%d (%.4f%%) n40=%d x40=%d (%.4f%%) diff_pp=%.4f wald_ci_pp=[%.4f, %.4f] z=%.4f p=%.6f\n",
      col, n30, x30, 100*p30, n40, x40, 100*p40, 100*(p40-p30), 100*(p40-p30-z*se_w), 100*(p40-p30+z*se_w), zt, 2*pnorm(-abs(zt))))
}
cmp("r1"); cmp("r7")
exp <- (n30 + n40) * c(alloc30, 1 - alloc30)
chi <- sum((c(n30, n40) - exp)^2/exp)
cat(sprintf("SRM (assumed gate_30 share=%.2f): chi2=%.4f df=1 p=%.6f\n", alloc30, chi, pchisq(chi, 1, lower.tail = FALSE)))
