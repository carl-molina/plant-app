"use strict";

const BASE_URL = '/api/get-plant-list';
const DEFAULT_IMG_URL = '/static/images/sadplant.png';
const DEFAULT_UPGRADE_TEXT = 'upgrade API plan';

const $resultsArea = $("#resultsArea");
const $searchForm = $("#search-form");

let plantId = '';

/** processSearchForm: handle submission of form:
 *
 * - make API call to server to get list of plants matching search term
 * - show errors, if errors are returned
 * - else: show results
 */

async function processSearchForm() {
  console.log('We got into processSearchForm!');
  console.debug('processSearchForm ran!');

  const term = $("#plant-search").val();
  console.log('This is term', term);

  const formData = await fetch(BASE_URL, {
    method: "POST",
    body: JSON.stringify({term}),
    headers: {
      "Content-Type": "application/json"
    }
  });

  const plantData = await formData.json();
  console.log('This is plantData', plantData);

  const plants = [];
  for (const plant of plantData.data) {
    let {
      id,
      common_name,
      scientific_name,
      cycle,
      watering,
      sunlight,
      default_image,
    } = plant;

    if (default_image === null ||
      default_image.medium_url ===
      "https://perenual.com/storage/image/upgrade_access.jpg") {
        default_image = DEFAULT_IMG_URL;
    } else if (default_image.medium_url === undefined) {
      default_image = default_image.original_url;
    } else {
      default_image = default_image.medium_url;
    }

    if (cycle ===
      ("Upgrade Plans To Premium/Supreme - " +
      "https://perenual.com/subscription-api-pricing. I'm sorry")
      ) {
        cycle = DEFAULT_UPGRADE_TEXT;
      }

    if (watering ===
      ("Upgrade Plans To Premium/Supreme - " +
      "https://perenual.com/subscription-api-pricing. I'm sorry")
      ) {
        watering = DEFAULT_UPGRADE_TEXT;
      }

    if (sunlight ===
      ("Upgrade Plans To Premium/Supreme - " +
      "https://perenual.com/subscription-api-pricing. I'm sorry")
      ) {
        sunlight = DEFAULT_UPGRADE_TEXT;
      }

    plants.push(
      {
        id,
        common_name,
        scientific_name,
        cycle,
        watering,
        sunlight,
        default_image,
      }
    );
  }

  return plants;

  // TODO: after successful storing of plants into an array, displayPlants(plants)!!
  // separation of concerns; display plants is a UI concern
  // ^ this function is concerned w/ pulling data from the API instead of UI

  if (plantData['errors']) {
    removeError();
    removeResults();
    showError(plantData.error);
  }

  else {
    removeError();
    removeResults();
    showResults(plantData);
  }
}

/** showError: shows error message in DOM. */

function showError(error) {
  $searchErr.text(error.term);
  // ^ Need to make a searchErr area later (look up how lucky-nums did it)
}

/** removeError: removes error message in DOM. */

function removeError() {
  $("#search-err-area").empty();
}

/** removeResults: removes previous results in DOM. */

function removeResults() {
  $resultsArea.empty();
}

/** showResults: shows search results in the DOM.
 *
 *  data parameter is expecting an array of plant data with each item an
 *  individual plant
*/

function showResults(plants) {
  for (const plant of plants) {
    const result = generateResultsMarkup(plant);
    $resultsArea.append(result);
  }

}

/** generateResultsMarkup: generates markup for plant data. */

function generateResultsMarkup(plant) {
  console.log('This is plant.id', plant.id);
  return `
    <div class="card h-150 text-bg-secondary gx-0" style="max-width: 19rem">
      <img
        src="${plant.default_image}"
        class="card-img-top"
        style="height: 16rem"
        alt="${plant.default_image} Image"
      >
        <div class="card-body">
          <h5 class="card-title">${plant.common_name}</h5>
          <form class="ml-0 d-inline">
          <input type="hidden" id="plant-id" name="plant-id" value="${plant.id}">
          <button id="unlike-${plant.id}" style="display: none"
            class="btn-sm btn btn-link">
            <i class="bi bi-bookmark-fill"></i>
          </button>
          <button id="like-${plant.id}" style="display: none"
            class="btn-sm btn btn-link">
            <i class="bi bi-bookmark"></i>
          </button>
        </form>
          <p class="card-text">Scientific Name: ${plant.scientific_name}</p>
          <p class="card-text">Cycle: ${plant.cycle}</p>
          <p class="card-text">Watering: ${plant.watering}</p>
          <p class="card-text">Sunlight: ${plant.sunlight}</p>
          <a href="/plants/${plant.id}" class="card-text"><i>More Details</i></a>
        </div>
      </div>

      <script>
        plantId = ${plant.id};
        console.log('This is plantId from search.js', plantId);
        checkLikes(${plant.id});
      </script>
  `;
}


async function processFormDataDisplayResults(evt) {
  evt.preventDefault();
  $resultsArea.empty();
  const plants = await processSearchForm();
  showResults(plants);

}

$searchForm.on("submit", processFormDataDisplayResults);