from datetime import datetime, timedelta
import traceback
from config import ALL_CRYPTO_PAIRS
from coco_handler import CocoHandler
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from rv_session import RVSession
from history_handler import HistoryHandler
from diversity_handler import DiversityHandler, read_image_from_url
from crypto_handler import CryptoHandler
from error_handler import handle_errors

from freqtrade_handler import FreqtradeHandler
import threading
from multiprocessing import Process
import signal
import os
import sys
from gpt_handler import GPTHandler


def run_web_app():
    # select the subset of crypto_pairs we use for the session from the larger set
    app = Flask(__name__)
    app.secret_key = 'aa2df4051ded7e95ac50c0dbf3f78a2b'
    history_handler = HistoryHandler("./history")
    crypto_handler = CryptoHandler(stake_currency='USDT',
                                   freqtrade_handler=FreqtradeHandler())
    coco_handler = CocoHandler()

    gpt_handler = GPTHandler()
    rv_session = RVSession(all_trading_pairs=ALL_CRYPTO_PAIRS,
                           coco_handler=coco_handler, crypto_handler=crypto_handler, gpt_handler=gpt_handler)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/start-session', methods=['GET', 'POST'])
    def start_session():
        if request.method == 'POST':
            # Print the form data to see what's being sent
            print(f'start_session (form_data): {request.form}')
            try:
                # Fetch the form data
                start_time = request.form.get('start_time')
                end_time = request.form.get('end_time')
                n_cryptos_str = request.form.get('n_cryptos')
                show_length = request.form.get('show_length', '5')

                # Check if any of the values are None
                if None in [start_time, end_time, n_cryptos_str]:
                    flash('Please fill out all the required fields.', 'danger')
                    return redirect(url_for('start_session'))

                n_cryptos = int(n_cryptos_str)

                # You can now use these values in your logic

                # Store the end time in the session variable
                session['start_time'] = start_time
                session['end_time'] = end_time
                session['n_cryptos'] = n_cryptos
                session['show_length'] = show_length

                # Start the session
                rv_session.start_session(n_cryptos=n_cryptos)

                flash('Session started successfully!', 'success')
                return redirect(url_for('loading'))
            except Exception as e:
                flash(f'Error starting session: {str(e)}', 'danger')

        # Calculate default start and end times
        default_start_time = datetime.now() + timedelta(minutes=2)
        default_end_time = default_start_time + timedelta(minutes=5)

        # Format the times to fit the `datetime-local` input format: "YYYY-MM-DDTHH:MM"
        default_start_time_str = default_start_time.strftime('%Y-%m-%dT%H:%M')
        default_end_time_str = default_end_time.strftime('%Y-%m-%dT%H:%M')

        default_n_cryptos = 2

        return render_template('start_session.html', n_cryptos=default_n_cryptos, default_start_time=default_start_time_str, default_end_time=default_end_time_str)

    @app.route('/arv-session', methods=['GET', 'POST'])
    def arv_session():
        # ARV instructions
        instructions = f"""
        Remote Viewing Instructions:
        - Location: This computer screen
        - Time: {session.get('end_time')}
        - Duration: {session.get('show_length')} minutes
        """
        if request.method == 'POST':
            user_description = request.form.get('arv_input')
            if not user_description:
                flash("Please provide a description.", 'danger')
                return render_template('arv_session.html', instructions=instructions)

            # Store user's ARV insights in the RVSession
            rv_session.record_rv_session(user_description)

            # Use the RVSession's methods to find the matched crypto
            matched_crypto = rv_session.image_match()

            # Place a buy order for the matched crypto
            rv_session.buy_matched_crypto()

            return redirect(url_for('loading'))

        return render_template('arv_session.html', instructions=instructions)

    @app.route('/loading', methods=['GET'])
    def loading():
        current_time = datetime.now()
        start_time = datetime.strptime(session.get(
            'start_time', '9999-12-31T00:00'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(session.get(
            'end_time', '9999-12-31T23:59'), '%Y-%m-%dT%H:%M')

        # If current time is before start time, show the loading page with a message indicating we're waiting for the ARV session to start
        if current_time < start_time:
            time_remaining = start_time - current_time
            message = "Waiting for ARV Session to start..."
            return render_template('loading.html', time_remaining=str(time_remaining).split('.')[0], message=message)

        # If current time is between start and end time, show the loading page with a message indicating we're waiting for the results
        elif start_time <= current_time < end_time:
            time_remaining = end_time - current_time
            message = "ARV Session completed. Waiting to show results..."
            return render_template('loading.html', time_remaining=str(time_remaining).split('.')[0], message=message)

        # If current time is after the end time, redirect to show results
        else:
            return redirect(url_for('show_results'))

    @app.route('/show-results', methods=['GET'])
    def show_results():
        current_time = datetime.now()
        start_time = datetime.strptime(session.get(
            'start_time', '9999-12-31T00:00'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(session.get(
            'end_time', '9999-12-31T23:59'), '%Y-%m-%dT%H:%M')

        # If current time is before start time, show the loading page
        if current_time < start_time:
            time_remaining = start_time - current_time
            return render_template('loading.html', time_remaining=str(time_remaining).split('.')[0])

        # If current time is between start and end time, show the loading page if the user has already provided input
        elif start_time <= current_time < end_time:
            if rv_session.user_description is not None:  # User has provided input
                time_remaining = end_time - current_time
                return render_template('loading.html', time_remaining=str(time_remaining).split('.')[0])
            else:  # User hasn't provided input, start ARV session
                return redirect(url_for('arv_session'))

        # If current time is after the end time, place the sell order and then show the results
        else:
            rv_session.sell_matched_crypto()

        # Fetch and Display results
        crypto_performance_data = rv_session.crypto_handler.get_latest_data()
        top_crypto, top_growth = rv_session.crypto_handler.get_top_performing_crypto()
        matched_crypto, matched_crypto_growth = rv_session.matched_crypto, crypto_performance_data[
            rv_session.matched_crypto]['growth']

        top_image = rv_session.get_associated_image(top_crypto)
        image_url, image_caption_list = top_image["url"], top_image["caption_list"]

        results = {
            "matched_crypto": matched_crypto,
            "matched_crypto_growth": matched_crypto_growth,
            "top_crypto": top_crypto,
            "top_growth": top_growth,
            "image_url": image_url,
            "image_map": rv_session.crypto_image_map,
            "user_description": rv_session.user_description,
            "crypto_performance": crypto_performance_data,
            "start_time": start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "end_time": end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        # Save the session data to history file
        history_handler.save_session_data(results)

        return render_template('results.html', results=results)

    @app.route('/submit-session', methods=['POST'])
    def submit_session():
        session_data = request.form.get('data')

        flash('Session data submitted successfully!', 'success')
        return render_template('submit_session.html')

    @app.route('/reset', methods=['POST'])
    def reset_session():
        rv_session.reset_session()
        return redirect(url_for('index'))

    @app.errorhandler(Exception)
    def handle_all_exceptions(e):
        # Log the error and its traceback for debugging
        trace = traceback.format_exc()
        app.logger.error(f"Unhandled Exception: {str(e)}\nTraceback:\n{trace}")

        # Return a user-friendly error message
        # If in development, also return the traceback for more detailed debugging
        if app.debug:
            return jsonify(error="An unexpected error occurred.", traceback=trace), 500
        return jsonify(error="An unexpected error occurred. Please try again later."), 500

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify(error="Resource not found."), 404

    @app.route('/display_images')
    def display_images():
        handler = CocoHandler()
        img, captions = handler.get_random_image()

        images = [{
            'url': img['coco_url'],  # assuming this is a direct link
            'color_palette': img['color_palette'],
            'captions': captions
        }]

        # Add more images to list if needed

        return render_template('display_images.html', images=images)

    # Continuation in app.py

    @app.route('/test_diversity_handler')
    def test_diversity_handler():
        handler = CocoHandler()
        img_obj, captions = handler.get_random_image()
        raw_image = read_image_from_url(img_obj['coco_url'])

        diversity_handler = DiversityHandler()

        images = []

        # Parameters
        pixel_sizes = [5, 10, 15, 50,  75,  100]
        similarity_thresholds = [5, 10, 15, 50, 75, 100]
        apply_clusterings = [True, False]
        n_clusters_list = [1, 2, 3, 5,  8,  12]

        total_operations = len(pixel_sizes) * len(similarity_thresholds) * \
            len(apply_clusterings) * len(n_clusters_list)
        print(f"Total operations to be performed: {total_operations}")
        completed_operations = 0

        for pixel_size in pixel_sizes:
            for similarity_threshold in similarity_thresholds:
                for apply_clustering in apply_clusterings:
                    for n_clusters in n_clusters_list:

                        color_palette = diversity_handler.extract_palette(
                            img_obj, pixel_size=pixel_size, similarity_threshold=similarity_threshold,
                            apply_clustering=apply_clustering, n_clusters=n_clusters, raw_image=raw_image
                        )

                        images.append({
                            'url': img_obj['coco_url'],
                            'color_palette': color_palette,
                            'captions': [f"Pixel Size: {pixel_size}, Similarity Threshold: {similarity_threshold}, Apply Clustering: {apply_clustering}, N Clusters: {n_clusters}"]
                        })

                        completed_operations += 1
                        print(
                            f"Completed: {completed_operations}/{total_operations}")

        return render_template('display_images.html', images=images)

    # start web serving
    # use_reloader=False with multiprocessing
    app.run(debug=True, use_reloader=False)


def signal_handler(sig, frame):
    print('Terminating the processes...')
    sys.exit(0)


def run_freqtrade():
    FREQTRADE_DIR = "./freqtrade_wrapper"
    FREQTRADE_STRATEGY = 'CustomFreqtradeStrategy'
    FREQTRADE_CONFIG = '--config configs/config_backtest.json --config configs/config_static_pairlist.json'

    # run freqtrade live # NOTE: we 'ls' into FREQTRADE_DIR during this process.
    os.system(
        f'cd {FREQTRADE_DIR}; freqtrade trade --strategy {FREQTRADE_STRATEGY} {FREQTRADE_CONFIG}')


"""
# activate virtualenv linked to freqtrade

FREQTRADE_DIR = "~/Code/freqtrade"
print(f'source {FREQTRADE_DIR}/.venv/bin/activate')
os.system(f'source {FREQTRADE_DIR}/.venv/bin/activate')
"""
if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    web_process = Process(target=run_web_app)
    web_process.start()

    freqtrade_process = Process(target=run_freqtrade)
    freqtrade_process.start()

    while True:
        try:
            # Keep the main thread alive
            pass
        except KeyboardInterrupt:
            # Gracefully terminate the processes if Ctrl+C is pressed
            print("Terminating processes...")
            web_process.terminate()
            freqtrade_process.terminate()
            break
