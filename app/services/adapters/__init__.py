"""Vision/text adapters for the AgriGuard image analysis + assistant.

Each adapter implements the same contract so the rest of the pipeline is
agnostic to the underlying provider (mock vs OpenAI vs a future CNN).
"""
