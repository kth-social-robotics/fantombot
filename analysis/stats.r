library(lmerTest)
library(gplots)
library('dplyr')
​
​
df <- read.csv("path_to_csv")
options(width=200)
par(mfrow=c(1,10))
​
​
​
m1 <- lmer(likely_user_utterance ~ dataset_name + (1|annotator), data=df, REML=FALSE)
m2 <- lmer(likely_user_utterance ~ dataset_name + (1+dataset_name|annotator), data=df, REML=FALSE)
​
​
​
anova(m1, m2)
​
​
​
pdf('results.pdf')
# textplot( capture.output(df %>% group_by(dataset_name) %>% summarize(mean=mean(likely_user_utterance), var=var(likely_user_utterance), std=sd(likely_user_utterance), median=median(likely_user_utterance))))
​
fit_likely_user_utterance <- lmer(likely_user_utterance ~ dataset_name + (1|annotator), data=df)
​
summary(fit_likely_user_utterance)
​
​
diff_likely_user_utterance <- difflsmeans(fit_likely_user_utterance, test.effs = "dataset_name")
​
​
# par(mfrow=c(4,6))
textplot(capture.output(summary(fit_likely_user_utterance)), valign="top", halign = "center", cex=0.6)
textplot(capture.output(anova(fit_likely_user_utterance)), valign="top", halign = "center", cex=0.6)
# par(mfrow=c(1,6))
# cex
textplot(capture.output(diff_likely_user_utterance), valign="top", halign = "center", cex=0.4)
plot(diff_likely_user_utterance)
​
​
​
fit_continue_system_utterance <- lmer(continue_system_utterance ~ dataset_name + (1|participant), data=df)
diff_continue_system_utterance <- difflsmeans(fit_continue_system_utterance, test.effs = "dataset_name")
​
textplot(capture.output(summary(fit_continue_system_utterance)), cex=0.6)
textplot(capture.output(diff_continue_system_utterance), cex=0.4)
plot(diff_continue_system_utterance)
​
​
​
fit_coherent_system_utterance <- lmer(coherent_system_utterance ~ dataset_name + (1|participant), data=df)
diff_coherent_system_utterance <- difflsmeans(fit_coherent_system_utterance, test.effs = "dataset_name")
​
textplot(capture.output(summary(fit_coherent_system_utterance)), cex=0.6)
textplot(capture.output(diff_coherent_system_utterance), cex=0.4)
plot(diff_coherent_system_utterance)
​
​
​
fit_interesting_system_utterance <- lmer(interesting_system_utterance ~ dataset_name + (1|participant), data=df)
diff_interesting_system_utterance <- difflsmeans(fit_interesting_system_utterance, test.effs = "dataset_name")
​
textplot(capture.output(summary(fit_interesting_system_utterance)), cex=0.6)
textplot(capture.output(diff_interesting_system_utterance), cex=0.4)
plot(diff_interesting_system_utterance)
​
​
dev.off()