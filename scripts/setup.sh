#!/usr/bin/env bash
set -e
mkdir -p logs outputs results
mkdir -p data/source/train data/source/validate
mkdir -p data/age_5_11 data/age_12_18
mkdir -p adapters/3b/age_5_11 adapters/3b/age_12_18
mkdir -p adapters/1b/age_5_11 adapters/1b/age_12_18
mkdir -p adapters/fast/3b/age_5_11 adapters/fast/3b/age_12_18
mkdir -p adapters/fast/1b/age_5_11 adapters/fast/1b/age_12_18
mkdir -p adapters/qwen/age_5_11 adapters/qwen/age_12_18
mkdir -p adapters/qwen4bit/age_5_11 adapters/qwen4bit/age_12_18
mkdir -p adapters/qwen_standard/age_5_11 adapters/qwen_standard/age_12_18
mkdir -p adapters/qwen4bit_standard/age_5_11 adapters/qwen4bit_standard/age_12_18

# Create empty source JSONL stubs — paste your data into these
for category in emotional_reassurance faqs_general_curiosity hospital_rules_and_routines what_to_expect who_are_these_people; do
    touch data/source/train/${category}.jsonl
    touch data/source/validate/${category}.jsonl
done

echo "All required directories and data stub files created."
echo "Paste your training data into:  data/source/train/*.jsonl"
echo "Paste your validation data into: data/source/validate/*.jsonl"
