"""Optional RAGAS adapter. Requires explicit judge settings; scoring incurs API calls."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import project_config  # load project .env without printing secrets

async def score(args):
    from importlib.metadata import version
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import Faithfulness, FactualCorrectness, ContextRecall
    class TracedFactualCorrectness(FactualCorrectness):
        async def _verify_claims(self, claims, reference):
            entry = dict(claims=claims, compared_against=reference)
            self.trace.append(entry)
            output = await super()._verify_claims(claims, reference)
            entry['judgments'] = output.model_dump()
            return output

        async def _decompose_and_verify_claims(self, text_to_decompose, reference_text):
            before = len(self.trace)
            result = await super()._decompose_and_verify_claims(text_to_decompose, reference_text)
            if len(self.trace) == before:
                self.trace.append(dict(claims=[], compared_against=reference_text))
            return result
    required = ('JUDGE_MODEL_ID', 'JUDGE_API_KEY', 'JUDGE_BASE_URL')
    use_responses = getattr(args, 'openai_responses', False)
    if not use_responses and any(not os.getenv(k) for k in required):
        raise ValueError('Configure JUDGE_MODEL_ID, JUDGE_API_KEY and JUDGE_BASE_URL explicitly')
    rows = [json.loads(line) for line in Path(args.input).read_text(encoding='utf-8').splitlines() if line.strip()]
    if use_responses:
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError('Set OPENAI_API_KEY for the OpenAI Responses judge')
        judge_model = 'gpt-6.1-terra'
        client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'], base_url='https://api.openai.com/v1', timeout=120)

        class ResponsesJudge:
            async def agenerate(self, prompt, response_model):
                response = await client.responses.parse(
                    model=judge_model, input=prompt, text_format=response_model,
                    reasoning={'effort': 'none'}, temperature=0, max_output_tokens=4096,
                )
                if response.status != 'completed' or response.output_parsed is None:
                    raise ValueError('OpenAI judge did not return a complete structured response')
                return response.output_parsed

        llm = ResponsesJudge()
    else:
        judge_model = os.environ['JUDGE_MODEL_ID']
        client = AsyncOpenAI(api_key=os.environ['JUDGE_API_KEY'], base_url=os.environ['JUDGE_BASE_URL'], timeout=120)
        llm = llm_factory(judge_model, client=client, temperature=0, max_tokens=4096)
    factual_class = TracedFactualCorrectness if args.trace_factual else FactualCorrectness
    metrics = dict(faithfulness=Faithfulness(llm=llm),
                   factual_correctness=factual_class(llm=llm), context_recall=ContextRecall(llm=llm))
    if args.metric:
        metrics = {name: metric for name, metric in metrics.items() if name in args.metric}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as handle:
        for row in rows:
            result = dict(question_id=row['question_id'], ragas_version=version('ragas'),
                          judge_model=judge_model, metrics={},
                          input_sha256=hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
                          judge_temperature=0,
                          judge_max_tokens=4096,
                          manual_review_required=True)
            if use_responses:
                result.update(judge_endpoint='responses', judge_reasoning_effort='none')
            if row['status'] != 'ok':
                result['status'] = 'generation_error'
            elif not row['answerable']:
                # Abstention should not be mechanically scored as ordinary factual QA.
                result['status'] = 'requires_manual_abstention_review'
            else:
                result['status'] = 'scored'
                calls = dict(
                    faithfulness=dict(user_input=row['question'], response=row['answer'], retrieved_contexts=row['retrieved_contexts']),
                    factual_correctness=dict(response=row['answer'], reference=row['reference']),
                    context_recall=dict(user_input=row['question'], retrieved_contexts=row['retrieved_contexts'], reference=row['reference']))
                for name, metric in metrics.items():
                    if isinstance(metric, TracedFactualCorrectness):
                        metric.trace = []
                    try:
                        value = await metric.ascore(**calls[name])
                        result['metrics'][name] = dict(value=value.value, reason=getattr(value, 'reason', None))
                    except Exception as exc:
                        result['metrics'][name] = dict(value=None, error_type=type(exc).__name__)
                        result['status'] = 'partial_error'
                    if isinstance(metric, TracedFactualCorrectness):
                        result['metrics'][name]['trace'] = metric.trace
            handle.write(json.dumps(result, ensure_ascii=False, default=str) + '\n')
            handle.flush()
    await client.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--trace-factual', action='store_true')
    parser.add_argument('--openai-responses', action='store_true', help='Use GPT-6.1 Terra via OpenAI Responses')
    parser.add_argument('--metric', action='append', choices=['faithfulness', 'factual_correctness', 'context_recall'])
    args = parser.parse_args()
    asyncio.run(score(args))

if __name__ == '__main__':
    main()
