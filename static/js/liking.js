async function like(evt) {
  evt.preventDefault();

  const plantId = $(this).closest(".card-body").find(".plant-id").val();

// TODO: find a way to get the plant ID value here

  console.log('This is plantId', plantId);

  const response = await axios.post("/api/like", { plant_id: plantId });
  const result = response.data;

  if ("error" in result) {
    console.log(result.error);
  } else {
    $(`#like-${plantId}`).hide();
    $(`#unlike-${plantId}`).show();
  }
}

async function unlike(evt) {
  evt.preventDefault();

  const plantId = $(this).closest(".card-body").find(".plant-id").val();
  console.log('This is plantId', plantId);

  const response = await axios.post("/api/unlike", { plant_id: plantId });
  const result = response.data;

  if ("error" in result) {
    console.log(result.error);
  } else {
    $(`#unlike-${plantId}`).hide();
    $(`#like-${plantId}`).show();
  }
}


async function checkLikes(plantId) {
  console.debug('We got into checkLikes!', plantId);
  $(`#unlike-${plantId}`).on("click", unlike);
  $(`#like-${plantId}`).on("click", like);

  const response = await axios.get("/api/likes", {params: { plant_id: plantId }});
  const result = response.data;
  console.log('This is response.data', response.data);

  if ("error" in result) {
    console.log(result.error);
  } else {
    const likes = result.likes;
    if (likes) $(`#unlike-${plantId}`).show();
    else $(`#like-${plantId}`).show();
  }
}
