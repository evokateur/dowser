#!/usr/bin/env python3
import argparse
import logging
import sys
from stream_detector import StreamDetector
from clipboard_manager import ClipboardManager


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


def validate_url(url: str) -> str:
    if not url:
        raise ValueError("URL cannot be empty")

    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def main():
    parser = argparse.ArgumentParser(
        description="Find and report audio streams from a given URL", prog="dowser"
    )

    parser.add_argument("url", help="URL to analyze for audio streams")

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--list-all",
        action="store_true",
        help="List all found streams instead of just the best one",
    )

    parser.add_argument(
        "--no-clipboard",
        action="store_true",
        help="Do not copy the best stream URL to clipboard",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    try:
        url = validate_url(args.url)
        logging.info(f"Analyzing URL: {url}")

        detector = StreamDetector()

        if args.list_all:
            streams = detector.find_audio_streams(url)

            if not streams:
                print("No audio streams found.")
                sys.exit(1)

            print(f"Found {len(streams)} audio stream(s):")
            print("-" * 80)

            for i, stream in enumerate(streams, 1):
                print(f"{i}. {stream.url}")
                print(f"   Format: {stream.format}")
                print(f"   Quality Score: {stream.quality_score}")
                print()

            if not args.no_clipboard and streams:
                best_stream = streams[0]
                if ClipboardManager.copy_to_clipboard(best_stream.url):
                    print(f"Best stream URL copied to clipboard: {best_stream.url}")
                else:
                    print("Failed to copy to clipboard")

        else:
            best_stream = detector.get_best_stream(url)

            if not best_stream:
                print("No audio streams found.")
                sys.exit(1)

            print("Best audio stream found:")
            print(f"URL: {best_stream.url}")
            print(f"Format: {best_stream.format}")
            print(f"Quality Score: {best_stream.quality_score}")

            if not args.no_clipboard:
                if ClipboardManager.copy_to_clipboard(best_stream.url):
                    print("\nURL copied to clipboard!")
                else:
                    print("\nFailed to copy URL to clipboard")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)

    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
